#!/usr/bin/env python3
"""Download the complete pinned BoilingBench public archive.

This downloader uses direct GET requests and resumes safely at file boundaries.
It writes only to the requested external data directory; no archive data is
copied into the repository.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import deque
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "baselines" / "chfwatch" / "data_contract.json"


def manifest(repo_id: str, revision: str) -> list[dict[str, object]]:
    base = f"https://huggingface.co/api/datasets/{quote(repo_id, safe='/')}/tree/{revision}"
    queue: deque[str] = deque([base])
    seen_urls: set[str] = set()
    files_by_path: dict[str, dict[str, object]] = {}
    while queue:
        url = queue.popleft()
        if url in seen_urls:
            continue
        seen_urls.add(url)
        request = Request(url, headers={"User-Agent": "BoilingBench-archive-downloader/1.0"})
        with urlopen(request, timeout=120) as response:
            entries = json.load(response)
            link = response.headers.get("Link", "")
        next_match = re.search(r"<([^>]+)>;\s*rel=\"next\"", link)
        if next_match:
            queue.append(next_match.group(1))
        for entry in entries:
            if entry["type"] == "directory":
                queue.append(base + "/" + quote(entry["path"], safe="/"))
            elif entry["type"] == "file":
                files_by_path[entry["path"]] = entry
    return [files_by_path[path] for path in sorted(files_by_path)]


def download_file(url: str, target: Path, retries: int, sleep_s: float) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": "BoilingBench-archive-downloader/1.0"})
            with urlopen(request, timeout=300) as response, partial.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            os.replace(partial, target)
            return
        except HTTPError as exc:
            if partial.exists():
                partial.unlink()
            if exc.code != 429 or attempt == retries:
                raise
            retry_after = exc.headers.get("Retry-After")
            header_delay = float(retry_after) if retry_after and float(retry_after) > 0 else 0.0
            delay = min(max(header_delay, 30.0 * (2**attempt)), 300.0)
            print(f"rate limited; waiting {delay:.0f}s before retry", flush=True)
            time.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--sleep-s", type=float, default=0.10)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text())
    repo_id = contract["huggingface_dataset"]
    revision = contract["huggingface_revision"]
    entries = manifest(repo_id, revision)
    expected = contract["full_public_archive"]
    if len(entries) != expected["expected_file_count"]:
        raise SystemExit(f"manifest file count changed: {len(entries)} != {expected['expected_file_count']}")
    total_bytes = sum(int(entry.get("size") or 0) for entry in entries)
    if total_bytes != expected["expected_bytes"]:
        raise SystemExit(f"manifest byte count changed: {total_bytes} != {expected['expected_bytes']}")
    pending = []
    for entry in entries:
        target = args.data_root / entry["path"]
        if target.is_file() and target.stat().st_size == int(entry["size"]):
            continue
        pending.append(entry)
    print(f"manifest files={len(entries)} bytes={total_bytes} pending={len(pending)}")
    if args.dry_run:
        return
    for index, entry in enumerate(pending, start=1):
        path = entry["path"]
        url = f"https://huggingface.co/datasets/{repo_id}/resolve/{revision}/{quote(path, safe='/')}?download=true"
        print(f"[{index}/{len(pending)}] {path} ({entry['size']} bytes)", flush=True)
        download_file(url, args.data_root / path, args.retries, args.sleep_s)
        if (args.data_root / path).stat().st_size != int(entry["size"]):
            raise SystemExit(f"size mismatch after download: {path}")
        if args.sleep_s > 0:
            time.sleep(args.sleep_s)


if __name__ == "__main__":
    main()

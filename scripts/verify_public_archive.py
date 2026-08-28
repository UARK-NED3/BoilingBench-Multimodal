#!/usr/bin/env python3
"""Verify a local BoilingBench archive against its pinned Hub manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import deque
from pathlib import Path
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
        request = Request(url, headers={"User-Agent": "BoilingBench-archive-verifier/1.0"})
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-hash", action="store_true", help="skip local SHA-256 computation")
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text())
    repo_id = contract["huggingface_dataset"]
    revision = contract["huggingface_revision"]
    entries = manifest(repo_id, revision)
    expected_paths = {entry["path"] for entry in entries}
    local_files = {
        path.relative_to(args.data_root).as_posix()
        for path in args.data_root.rglob("*")
        if path.is_file() and not path.relative_to(args.data_root).parts[0:1] == (".cache",)
    }
    missing: list[str] = []
    size_mismatches: list[dict[str, object]] = []
    files: list[dict[str, object]] = []
    for entry in entries:
        path = args.data_root / entry["path"]
        record: dict[str, object] = {
            "path": entry["path"],
            "expected_bytes": int(entry["size"]),
            "hub_oid": entry.get("oid"),
        }
        if not path.is_file():
            missing.append(entry["path"])
            record["status"] = "missing"
        else:
            actual = path.stat().st_size
            record["actual_bytes"] = actual
            if actual != int(entry["size"]):
                size_mismatches.append({"path": entry["path"], "expected": int(entry["size"]), "actual": actual})
                record["status"] = "size_mismatch"
            else:
                record["status"] = "pass"
                if not args.no_hash:
                    record["sha256"] = sha256(path)
        files.append(record)
    report = {
        "repo_id": repo_id,
        "revision": revision,
        "expected_file_count": len(entries),
        "expected_bytes": sum(int(entry["size"]) for entry in entries),
        "local_file_count_excluding_cache": len(local_files),
        "local_bytes_excluding_cache": sum((args.data_root / path).stat().st_size for path in local_files),
        "missing_count": len(missing),
        "size_mismatch_count": len(size_mismatches),
        "extra_count": len(local_files - expected_paths),
        "missing": missing,
        "size_mismatches": size_mismatches,
        "extra": sorted(local_files - expected_paths),
        "status": "pass" if not missing and not size_mismatches and not (local_files - expected_paths) else "fail",
        "files": files,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "expected_file_count", "expected_bytes", "local_file_count_excluding_cache", "local_bytes_excluding_cache", "missing_count", "size_mismatch_count", "extra_count")}, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Generate a file manifest for BoilingBench-Multimodal."""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.', help='Root to inventory')
    parser.add_argument('--output', default='MANIFEST.csv')
    parser.add_argument('--checksums', action='store_true', help='Compute SHA256 checksums')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rows = []
    excluded_parts = {'.git', '__pycache__', 'raw_archives'}
    for path in sorted(root.rglob('*')):
        if path.is_file() and not (excluded_parts & set(path.parts)):
            rel = path.relative_to(root).as_posix()
            rows.append({
                'path': rel,
                'bytes': path.stat().st_size,
                'sha256': sha256(path) if args.checksums else '',
            })

    out = Path(args.output)
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'bytes', 'sha256'])
        writer.writeheader()
        writer.writerows(rows)

    print(f'wrote {len(rows)} rows to {out}')


if __name__ == '__main__':
    main()

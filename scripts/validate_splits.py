#!/usr/bin/env python
"""Validate that split files do not assign a run_id to multiple splits."""
from __future__ import annotations

import csv
from pathlib import Path


def main() -> None:
    split_dir = Path('splits')
    seen = {}
    errors = []
    for path in sorted(split_dir.glob('*.csv')):
        with path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required = {'dataset_id', 'run_id', 'split'}
            missing = required - set(reader.fieldnames or [])
            if missing:
                errors.append(f'{path}: missing columns {sorted(missing)}')
                continue
            for row in reader:
                key = (row['dataset_id'], row['run_id'])
                split = row['split']
                if key in seen and seen[key] != split:
                    errors.append(f'{key} appears in both {seen[key]} and {split}')
                seen[key] = split
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'validated {len(seen)} unique dataset/run assignments')


if __name__ == '__main__':
    main()

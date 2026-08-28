#!/usr/bin/env python
"""Generate leave-one-surface-out split files for NED3-007.

Reads the run->surface mapping from MANIFEST_NED3_007_FILES.csv and emits
one `splits/ned3-007-lso-surface-<surface>.csv` per surface. Each file
assigns every Boiling bench run to train or test, with the held-out
surface's runs as test.

Run ids are the BoilingBench run folders (`<surface prefix>_B<NN>`) found
under `Steady State/` and `Transient/` in the dataset archives. The surface
keys match the chf-watch surface vocabulary.

Usage:
    python scripts/make_ned3_007_lso_splits.py [--manifest MANIFEST_NED3_007_FILES.csv] [--out splits]
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

# BoilingBench directory prefix -> NED3-007 surface key (matches chf-watch).
FOLDER_PREFIX_TO_SURFACE = {
    "PH0": "cu_foam_pH0",
    "PH10": "cu_foam_pH10",
    "PH12": "cu_foam_pH12",
    "Polished Cu": "polished_cu",
    "Polished MC": "microchannel",
}

SURFACES = ["cu_foam_pH0", "cu_foam_pH10", "cu_foam_pH12", "microchannel", "polished_cu"]

RUN_FOLDER_RE = re.compile(r"/(?:Steady State|Transient)/(.+?/)?(PH\d+|Polished Cu|Polished MC)_(B\d+)/")


def collect_runs(manifest_path: Path) -> dict[str, list[str]]:
    """Return surface -> sorted run ids (Boiling-NN) from the file manifest."""
    runs: dict[str, set[str]] = {s: set() for s in SURFACES}
    with manifest_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = RUN_FOLDER_RE.search(row.get("path", ""))
            if not m:
                continue
            prefix = m.group(2) or m.group(1)
            # Archive run token, verbatim from the dataset folder name
            # (e.g. `Steady State/PH0_B69/` -> run_id `B69`).
            run_id = m.group(3)
            surface = FOLDER_PREFIX_TO_SURFACE.get(prefix)
            if surface is None or surface not in runs:
                continue
            runs[surface].add(run_id)
    return {s: sorted(v) for s, v in runs.items()}


def emit_split(surface: str, run_map: dict[str, list[str]], out_dir: Path) -> None:
    test_runs = sorted(run_map[surface])
    out = out_dir / f"ned3-007-lso-surface-{surface}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset_id", "run_id", "split", "task", "notes"])
        for run in test_runs:
            w.writerow([
                "ned3-007",
                run,
                "test",
                "multimodal_fusion",
                f"leave-one-surface-out; held-out surface: {surface}",
            ])
    total = sum(len(v) for v in run_map.values())
    print(f"wrote {out} (test={test_runs}; train = the {total - len(test_runs)} other runs)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="MANIFEST_NED3_007_FILES.csv", type=Path)
    p.add_argument("--out", default="splits", type=Path)
    args = p.parse_args()

    run_map = collect_runs(args.manifest)
    empty = [s for s in SURFACES if not run_map[s]]
    if empty:
        raise SystemExit(f"no runs found for surface(s): {empty}; check --manifest")

    args.out.mkdir(parents=True, exist_ok=True)
    for surface in SURFACES:
        emit_split(surface, run_map, args.out)


if __name__ == "__main__":
    main()
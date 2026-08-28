#!/usr/bin/env python
"""Generate leave-one-surface-out split files for BoilingBench-3/4 (multimodal runs).

Reads the run->surface mapping from the repo's run-level manifest and emits
one `splits/lso-surface-<surface>.csv` per surface. Each file assigns every
run to train or test, with the held-out surface's runs as test.

Dataset identity (per NED3 maintainers, 2026-06-03): the multimodal boiling
runs are distributed in the current benchmark as **BoilingBench-3** (Cu-foam
surfaces) and **BoilingBench-4** (flat-Cu surfaces), which come from NED3-002
— not NED3-007 (a steady-state-only set dropped from the benchmark). Run ids
here are the BoilingBench run folders (`<surface prefix>_B<NN>`) found under
`Steady State/` and `Transient/` in the archive. The surface keys match the
chf-watch surface vocabulary.

Run resolution currently reads `MANIFEST_NED3_007_FILES.csv` — a legacy
staging manifest (named for the earlier development-stage archive path
`ned3-007_MultimodalBoilingData`) that is still checked into this repo.
The current-version distribution replaces that archive with the BoilingBench
datasets hosted on Hugging Face / Zenodo / Dryad; if maintainers point the
run-level manifest at that revision, re-run here and the mapping is unchanged.

Usage:
    python scripts/make_lso_splits.py [--manifest MANIFEST_NED3_007_FILES.csv] [--out splits]
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

# BoilingBench directory prefix -> surface key (matches chf-watch vocabulary).
FOLDER_PREFIX_TO_SURFACE = {
    "PH0": "cu_foam_pH0",
    "PH10": "cu_foam_pH10",
    "PH12": "cu_foam_pH12",
    "Polished Cu": "polished_cu",
    "Polished MC": "microchannel",
}

# Surface -> current-benchmark dataset id (NED3-002 origin per maintainers).
# microchannel is flat-copper family (BoilingBench-4) but not named on the
# BBB-4 card; flagged for maintainer confirmation.
SURFACE_TO_DATASET = {
    "cu_foam_pH0": "BoilingBench-3",
    "cu_foam_pH10": "BoilingBench-3",
    "cu_foam_pH12": "BoilingBench-3",
    "polished_cu": "BoilingBench-4",
    "microchannel": "BoilingBench-4",
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
    dataset_id = SURFACE_TO_DATASET[surface]
    test_runs = sorted(run_map[surface])
    out = out_dir / f"lso-surface-{surface}.csv"
    confirm_mc = "confirm microchannel->BoilingBench-4" if surface == "microchannel" else ""
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset_id", "run_id", "split", "task", "notes"])
        for run in test_runs:
            w.writerow([
                dataset_id,
                run,
                "test",
                "multimodal_fusion",
                "leave-one-surface-out; held-out surface: "
                f"{surface}{'; ' + confirm_mc if confirm_mc else ''}",
            ])
    total = sum(len(v) for v in run_map.values())
    print(f"wrote {out} (dataset={dataset_id}; test={test_runs}; "
          f"train = the {total - len(test_runs)} other runs)")


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
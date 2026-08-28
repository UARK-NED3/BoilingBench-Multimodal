"""Thin adapter between BoilingBench-Multimodal and the standalone CHF-Watch repo.

This package does NOT vendor CHF-Watch source. It imports the pinned
`chfwatch` distribution and wraps it so that BoilingBench task definitions
and split files can drive it. Pin the standalone repo with:

    pip install "git+https://gitlab.com/moore.brad.m-group/chf-watch.git@b86bf0d"

The two useful entry points:

  * `run_to_surface(run_id, manifest) -> surface`  -- resolve a BoilingBench
    run id to the NED3-007 surface key it belongs to, using only the archive
    manifest (single source of truth).
  * `load_surface_split(csv_path, manifest) -> (train_surfaces, test_surfaces)`
    -- turn one leave-one-surface-out split file into the surface sets that
    drive CHF-Watch's group-held-out evaluation.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

# Dataset archive folder prefix -> NED3-007 surface key.
FOLDER_PREFIX_TO_SURFACE = {
    "PH0": "cu_foam_pH0",
    "PH10": "cu_foam_pH10",
    "PH12": "cu_foam_pH12",
    "Polished Cu": "polished_cu",
    "Polished MC": "microchannel",
}

SURFACES = ("cu_foam_pH0", "cu_foam_pH10", "cu_foam_pH12", "microchannel", "polished_cu")

_RUN_FOLDER_RE = re.compile(r"/(?:Steady State|Transient)/(.+?/)?(PH\d+|Polished Cu|Polished MC)_(B\d+)/")


def run_to_surface_map(manifest: str | Path) -> dict[str, str]:
    """Map every run id present in the archive manifest to its surface key."""
    out: dict[str, str] = {}
    with Path(manifest).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = _RUN_FOLDER_RE.search(row.get("path", ""))
            if not m:
                continue
            prefix = m.group(2) or m.group(1)
            surface = FOLDER_PREFIX_TO_SURFACE.get(prefix)
            if surface is not None:
                out[m.group(3)] = surface
    return out


def load_surface_split(split_csv: str | Path,
                       manifest: str | Path,
                       all_surfaces: Iterable[str] = SURFACES) -> tuple[list[str], list[str]]:
    """Return (train_surfaces, test_surfaces) for a leave-one-surface-out file.

    `all_surfaces` must be the complete NED3-007 surface set. The split file
    lists only the held-out test runs (see splits/README); training surfaces
    are the complement over the manifest's run->surface map.
    """
    split_csv = Path(split_csv)
    run_surface = run_to_surface_map(manifest)

    test_runs: list[str] = []
    with split_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("split") == "test":
                test_runs.append(row["run_id"])

    unknown = [r for r in test_runs if r not in run_surface]
    if unknown:
        raise ValueError(f"run ids in {split_csv.name} not found in manifest: {sorted(unknown)}")

    test_surfaces = sorted({run_surface[r] for r in test_runs})
    train_surfaces = [s for s in all_surfaces if s not in test_surfaces]
    return train_surfaces, test_surfaces
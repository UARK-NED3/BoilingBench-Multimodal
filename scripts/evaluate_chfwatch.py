#!/usr/bin/env python
"""Evaluate the CHF-Watch reference baseline on one leave-one-surface-out fold.

Binds a `splits/ned3-007-lso-surface-<surface>.csv` file to the standalone
CHF-Watch pipeline (pinned at `b86bf0d`) and produces the standard
metadata/metrics record for that fold. Nothing is vendored here; the
benchmark script delegates the actual evaluation to the standalone repo's
E21 (LSO-calibrated) detector run, then writes metrics in the benchmark's
JSON layout.

Reported numbers are PROVISIONAL until independently reproduced by the
benchmark maintainers on repo-defined runs and split files (see
baselines/chfwatch/README.md).

Usage:
    python scripts/evaluate_chfwatch.py --split splits/ned3-007-lso-surface-cu_foam_pH0.csv \
        --manifest MANIFEST_NED3_007_FILES.csv \
        --repo ~/chf-watch --data-root <ned3-007 archive root> \
        --cache-root <feature cache> --out results/fold_cu_foam_pH0.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _require_chfwatch() -> tuple[object, str]:
    """Import and version-check the pinned chfwatch distribution."""
    try:
        import chfwatch  # noqa: F401
        from chfwatch.deploy import ChfWatchDetector  # noqa: F401
    except ImportError:
        sys.exit(
            "chfwatch is not installed. Install the pinned commit with:\n"
            "  pip install \"git+https://gitlab.com/moore.brad.m-group/chf-watch.git@b86bf0d\""
        )
    from importlib.metadata import version
    try:
        ver = version("chfwatch")
    except Exception:  # pragma: no cover - metadata unavailable on older setups
        ver = "unknown"
    return ChfWatchDetector, ver


def _load_split(split_csv: Path, manifest: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "baselines" / "chfwatch"))
    from adapter import load_surface_split
    return load_surface_split(split_csv, manifest)


def _run_standalone_e21(args, chfwatch_dir: Path, out_dir: Path) -> dict:
    """Run the standalone repo's E21 LSO-calibrated detector and return its dict."""
    sys.path.insert(0, str(chfwatch_dir / "scripts"))
    from run_e21_lso_calibrated_detector import run  # type: ignore[import-not-found]

    return run(
        data_root=str(args.data_root),
        out_dir=str(out_dir),
        cache_root=str(args.cache_root),
        max_far_cal=args.max_far_cal,
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--split", required=True, type=Path, help="one ned3-007-lso-surface-*.csv file")
    p.add_argument("--manifest", default=Path("MANIFEST_NED3_007_FILES.csv"), type=Path)
    p.add_argument("--repo", required=True, type=Path, help="standalone chf-watch checkout (pinned b86bf0d)")
    p.add_argument("--data-root", required=True, type=Path, help="extracted ned3-007 archive root (ae/ etc.)")
    p.add_argument("--cache-root", default=Path("data/processed/ned3_007"), type=Path)
    p.add_argument("--max-far-cal", type=float, default=0.05)
    p.add_argument("--out", required=True, type=Path, help="output metrics JSON")
    p.add_argument("--status", choices=["provisional"], default="provisional")
    args = p.parse_args()

    _, chf_version = _require_chfwatch()
    train_surfaces, test_surfaces = _load_split(args.split, args.manifest)

    out_dir = args.out.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    results = _run_standalone_e21(args, args.repo.resolve(), out_dir)

    held = test_surfaces[0]
    fold = next((f for f in results.get("folds", []) if f["held_out_surface"] == held), None)
    if fold is None:
        sys.exit(f"standalone E21 output has no fold for held-out surface {held!r}")

    record = {
        "baseline": "chfwatch",
        "standalone_commit": "b86bf0d",
        "chfwatch_version": chf_version,
        "split_file": str(args.split),
        "task": "multimodal_fusion",
        "train_surfaces": train_surfaces,
        "test_surfaces": test_surfaces,
        "status": args.status,
        "fold": {
            "held_out_surface": held,
            "recall": fold["held_metrics"]["recall"],
            "median_lead_s": fold["held_metrics"]["median_lead"],
            "far": fold["held_metrics"]["far"],
            "high_ss_trigger_rate": fold["held_metrics"]["high_ss_trigger_rate"],
        },
    }
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Run CHF-Watch's exploratory baseline on public BB-3/BB-4 processed data."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "baselines" / "chfwatch"))
from current_data import BIN_S, FEATURES, HF_REVISION, load_processed_case  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True, help="directory containing BB-3/ and BB-4/")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = {name: load_processed_case(args.data_root / name) for name in ("BB-3", "BB-4")}
    result = {
        "baseline": "chfwatch-current-data",
        "protocol": "leave-one-dataset-out",
        "hf_revision": HF_REVISION,
        "bin_s": BIN_S,
        "features": list(FEATURES),
        "target": "processed_heat_flux_W_cm2",
        "target_status": "screening-level processed target; not a confirmed CHF label",
        "folds": [],
    }
    for test_name, (test, meta) in cases.items():
        train_name = next(name for name in cases if name != test_name)
        train, _ = cases[train_name]
        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        model.fit(train[list(FEATURES)], train["heat_flux_W_cm2"])
        prediction = model.predict(test[list(FEATURES)])
        result["folds"].append({
            "train_dataset": train_name,
            "test_dataset": test_name,
            "n_train": len(train),
            "n_test": len(test),
            "mae_W_cm2": float(mean_absolute_error(test["heat_flux_W_cm2"], prediction)),
            "r2": float(r2_score(test["heat_flux_W_cm2"], prediction)),
            "train_only_scaling": True,
            "marker_metadata": meta,
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

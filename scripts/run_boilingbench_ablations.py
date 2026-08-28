#!/usr/bin/env python3
"""Run reproducible cross-dataset modality ablations for current BoilingBench.

Each fold holds out one dataset and trains on all other eligible datasets.
Modality sets are evaluated only where every case has the requested input;
missing microphones are never imputed as if they had been recorded.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "baselines" / "chfwatch"))
from current_data import (  # noqa: E402
    AE_FEATURES,
    AE_WAVEFORM_FEATURES,
    BIN_S,
    COMMON_FEATURES,
    HYDROPHONE_FEATURES,
    HF_REVISION,
    MICROPHONE_FEATURES,
    THERMAL_FEATURES,
    load_processed_case,
)

ABLATIONS = {
    "thermal_only": THERMAL_FEATURES,
    "hydrophone_only": HYDROPHONE_FEATURES,
    "ae_hits_only": AE_FEATURES,
    "ae_waveform_only": AE_WAVEFORM_FEATURES,
    "thermal_hydrophone": THERMAL_FEATURES + HYDROPHONE_FEATURES,
    "thermal_hydrophone_ae_hits": COMMON_FEATURES,
    "thermal_hydrophone_ae_waveform": THERMAL_FEATURES + HYDROPHONE_FEATURES + AE_WAVEFORM_FEATURES,
    "thermal_hydrophone_microphone_ae_hits": COMMON_FEATURES + MICROPHONE_FEATURES,
}
DATASETS = ("BB-1", "BB-2", "BB-3", "BB-4")


def score_fold(train, test, features: tuple[str, ...]) -> dict[str, float]:
    x_train, x_test = train[list(features)], test[list(features)]
    y_train, y_test = train["heat_flux_W_cm2"], test["heat_flux_W_cm2"]
    constant = float(y_train.mean())
    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model.fit(x_train, y_train)
    prediction = model.predict(x_test)
    return {
        "constant_mae_W_cm2": float(mean_absolute_error(y_test, [constant] * len(y_test))),
        "ridge_mae_W_cm2": float(mean_absolute_error(y_test, prediction)),
        "ridge_r2": float(r2_score(y_test, prediction)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = {
        "baseline": "chfwatch-current-data-ablations",
        "protocol": "leave-one-dataset-out; train on all other eligible datasets",
        "hf_revision": HF_REVISION,
        "bin_s": BIN_S,
        "target": "processed_heat_flux_W_cm2",
        "target_status": "screening-level processed target; not a confirmed CHF label",
        "target_provenance_note": "The release describes heat flux as a derived analysis product; thermal features are co-derived from the same thermal series, so metrics are not independent physical validation.",
        "target_not_used_as_feature": True,
        "ablations": {},
    }
    for name, features in ABLATIONS.items():
        loaded = {}
        for dataset in DATASETS:
            frame, metadata = load_processed_case(args.data_root / dataset, required_features=features)
            if frame.empty:
                continue
            loaded[dataset] = (frame, metadata)
        entry = {"features": list(features), "eligible_datasets": sorted(loaded), "folds": []}
        if len(loaded) < 2:
            entry["status"] = "insufficient eligible datasets"
            result["ablations"][name] = entry
            continue
        entry["status"] = "exploratory"
        for test_name, (test, test_meta) in loaded.items():
            train_frames = [frame for dataset, (frame, _meta) in loaded.items() if dataset != test_name]
            train = pd.concat(train_frames, ignore_index=True)
            metrics = score_fold(train, test, features)
            entry["folds"].append({
                "train_datasets": [dataset for dataset in loaded if dataset != test_name],
                "test_dataset": test_name,
                "n_train": len(train),
                "n_test": len(test),
                "train_only_scaling": True,
                "marker_metadata": test_meta,
                **metrics,
            })
        result["ablations"][name] = entry
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Train a CUDA temporal regressor on the four current BoilingBench runs.

The model uses resampled thermocouple and pressure sequences and holds out an
entire dataset for each fold. Heat flux remains a derived analysis target, so
this is a GPU regression diagnostic rather than a confirmed-CHF detector.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "baselines" / "chfwatch"))
from current_data import CONTRACT  # noqa: E402


DATASETS = ("BB-1", "BB-2", "BB-3", "BB-4")
FEATURE_NAMES = (
    "thermocouple_1_C",
    "thermocouple_2_C",
    "thermocouple_3_C",
    "thermocouple_4_C",
    "pressure_kPa_interpolated",
)


def locate_case(root: Path, dataset: str) -> Path:
    full = root / CONTRACT["datasets"][dataset]["directory"]
    if (full / "thermal_timeseries.npz").is_file():
        return full
    short = root / dataset
    if (short / "thermal_timeseries.npz").is_file():
        return short
    raise FileNotFoundError(f"thermal_timeseries.npz not found for {dataset}")


def resample_case(root: Path, dataset: str, target_hz: float) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    case_dir = locate_case(root, dataset)
    with np.load(case_dir / "thermal_timeseries.npz", allow_pickle=False) as arrays:
        source_time = np.asarray(arrays["time_reference_temperature_s"], dtype=float)
        end = float(source_time[-1])
        time_s = np.arange(float(source_time[0]), end + 0.5 / target_hz, 1.0 / target_hz)
        values = []
        for name in FEATURE_NAMES:
            source = np.asarray(arrays[name], dtype=float)
            values.append(np.interp(time_s, source_time, source))
        target = np.interp(time_s, source_time, np.asarray(arrays["heat_flux_W_cm2"], dtype=float))
    features = np.asarray(values, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    valid = np.isfinite(features).all(axis=0) & np.isfinite(target)
    features, target, time_s = features[:, valid], target[valid], time_s[valid]
    return features, target, {
        "dataset": dataset,
        "duration_s": float(time_s[-1] - time_s[0]),
        "samples_after_resampling": int(len(target)),
        "native_case_path": str(case_dir.relative_to(root)) if case_dir.is_relative_to(root) else case_dir.name,
        "native_median_dt_s": float(np.median(np.diff(source_time))),
    }


def make_windows(features: np.ndarray, target: np.ndarray, sequence_length: int, stride: int) -> tuple[np.ndarray, np.ndarray]:
    starts = range(0, len(target) - sequence_length + 1, stride)
    x = np.stack([features[:, start : start + sequence_length] for start in starts]).astype(np.float32)
    y = np.asarray([target[start + sequence_length - 1] for start in starts], dtype=np.float32)
    return x, y


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class TemporalRegressor(torch.nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.body = torch.nn.Sequential(
            torch.nn.Conv1d(channels, 64, 5, padding=2),
            torch.nn.BatchNorm1d(64),
            torch.nn.GELU(),
            torch.nn.Conv1d(64, 96, 5, padding=4, dilation=2),
            torch.nn.BatchNorm1d(96),
            torch.nn.GELU(),
            torch.nn.Conv1d(96, 128, 5, padding=8, dilation=4),
            torch.nn.BatchNorm1d(128),
            torch.nn.GELU(),
            torch.nn.AdaptiveAvgPool1d(1),
        )
        self.head = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(128, 64),
            torch.nn.GELU(),
            torch.nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.body(x)).squeeze(1)


def score(target: np.ndarray, prediction: np.ndarray, baseline: float) -> dict[str, float | int]:
    error = prediction - target
    total = float(np.sum((target - target.mean()) ** 2))
    return {
        "n": int(len(target)),
        "baseline_mae_W_cm2": float(np.mean(np.abs(target - baseline))),
        "mae_W_cm2": float(np.mean(np.abs(error))),
        "rmse_W_cm2": float(np.sqrt(np.mean(error**2))),
        "r2": float(1.0 - np.sum(error**2) / total) if total > 0 else 0.0,
    }


def fit_fold(train_x, train_y, test_x, test_y, args, seed: int, device, train_datasets, test_dataset):
    seed_everything(seed)
    train_mean = train_x.mean(axis=(0, 2), keepdims=True)
    train_scale = train_x.std(axis=(0, 2), keepdims=True)
    train_scale[train_scale < 1e-6] = 1.0
    target_mean = float(train_y.mean())
    target_scale = float(train_y.std()) or 1.0
    train_x = (train_x - train_mean) / train_scale
    test_x = (test_x - train_mean) / train_scale
    train_y_scaled = (train_y - target_mean) / target_scale
    train_tensor = torch.utils.data.TensorDataset(
        torch.from_numpy(train_x), torch.from_numpy(train_y_scaled.astype(np.float32))
    )
    generator = torch.Generator().manual_seed(seed)
    loader = torch.utils.data.DataLoader(
        train_tensor, batch_size=args.batch_size, shuffle=True, generator=generator,
        pin_memory=device.type == "cuda", num_workers=0,
    )
    model = TemporalRegressor(train_x.shape[1]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    loss_fn = torch.nn.SmoothL1Loss(beta=0.05)
    amp_enabled = bool(args.amp and device.type == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)
    started = time.perf_counter()
    for _epoch in range(args.epochs):
        model.train()
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device, non_blocking=True)
            batch_y = batch_y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp_enabled):
                loss = loss_fn(model(batch_x), batch_y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
    model.eval()
    with torch.no_grad():
        prediction = model(torch.from_numpy(test_x).to(device)).float().cpu().numpy()
    prediction = prediction * target_scale + target_mean
    result = score(test_y, prediction, target_mean)
    result.update({
        "seed": seed,
        "train_datasets": train_datasets,
        "test_dataset": test_dataset,
        "n_train": int(len(train_y)),
        "n_test": int(len(test_y)),
        "epochs": args.epochs,
        "train_seconds": float(time.perf_counter() - started),
        "train_only_feature_scaling": True,
        "train_only_target_scaling": True,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--target-hz", type=float, default=10.0)
    parser.add_argument("--sequence-length", type=int, default=128)
    parser.add_argument("--stride", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    device = torch.device("cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu")
    torch.set_float32_matmul_precision("high")
    cases = {dataset: resample_case(args.data_root, dataset, args.target_hz) for dataset in DATASETS}
    windows = {dataset: make_windows(features, target, args.sequence_length, args.stride) for dataset, (features, target, _meta) in cases.items()}
    folds = []
    for test_dataset in DATASETS:
        train_datasets = [dataset for dataset in DATASETS if dataset != test_dataset]
        train_x = np.concatenate([windows[dataset][0] for dataset in train_datasets])
        train_y = np.concatenate([windows[dataset][1] for dataset in train_datasets])
        test_x, test_y = windows[test_dataset]
        for seed in args.seeds:
            folds.append(fit_fold(train_x, train_y, test_x, test_y, args, seed, device, train_datasets, test_dataset))
    result = {
        "experiment": "gpu_temporal_heat_flux_regression",
        "contract_schema_version": CONTRACT["schema_version"],
        "release": CONTRACT["release"],
        "hf_revision": CONTRACT["huggingface_revision"],
        "data_root_label": args.data_root.name,
        "protocol": "leave-one-dataset-out; all windows from the held-out dataset stay unseen",
        "target": "processed_heat_flux_W_cm2",
        "target_note": "Derived analysis product from the thermal release; this is not independent physical CHF validation.",
        "features": list(FEATURE_NAMES),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "hyperparameters": {key: getattr(args, key) for key in ("target_hz", "sequence_length", "stride", "epochs", "batch_size", "learning_rate", "weight_decay", "amp")},
        "cases": {dataset: meta for dataset, (_features, _target, meta) in cases.items()},
        "window_counts": {dataset: int(len(windows[dataset][1])) for dataset in DATASETS},
        "folds": folds,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"experiment": result["experiment"], "device": result["device"], "gpu_name": result["gpu_name"], "window_counts": result["window_counts"], "folds": folds}, indent=2))


if __name__ == "__main__":
    main()

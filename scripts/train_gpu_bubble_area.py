#!/usr/bin/env python3
"""Train and evaluate a GPU bubble-area regressor on BoilingBench-5.

The split follows the public BubbleID base Train/Test directories. Flow-boiling
and new-facility images are kept as external-domain evaluations when present;
they are never mixed into fitting or validation.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "baselines" / "chfwatch"))
from current_data import CONTRACT  # noqa: E402


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png"}


class BubbleDataset(torch.utils.data.Dataset):
    def __init__(self, items: list[dict[str, object]], image_size: int, image_cache: dict[Path, torch.Tensor] | None = None) -> None:
        self.items = items
        self.image_size = image_size
        self.image_cache = image_cache if image_cache is not None else {}
        for item in self.items:
            path = item["image"]
            if path not in self.image_cache:
                with Image.open(path) as image:
                    image = image.convert("RGB").resize((image_size, image_size), Image.Resampling.BILINEAR)
                    array = np.asarray(image, dtype=np.float32).copy() / 255.0
                self.image_cache[path] = torch.from_numpy(array).permute(2, 0, 1)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        item = self.items[index]
        target = torch.tensor(item["area_fraction"], dtype=torch.float32)
        return self.image_cache[item["image"]], target


def polygon_area(points: list[list[float]]) -> float:
    if len(points) < 3:
        return 0.0
    x = np.asarray([point[0] for point in points], dtype=float)
    y = np.asarray([point[1] for point in points], dtype=float)
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0)


def record_for_image(image_path: Path, domain: str) -> dict[str, object]:
    annotation_path = image_path.with_suffix(".json")
    annotation = json.loads(annotation_path.read_text())
    with Image.open(image_path) as image:
        width, height = image.size
    width = float(annotation.get("imageWidth") or width)
    height = float(annotation.get("imageHeight") or height)
    shapes = [shape for shape in annotation.get("shapes", []) if str(shape.get("label", "")).startswith("bubble")]
    area = sum(polygon_area(shape.get("points", [])) for shape in shapes)
    return {
        "image": image_path,
        "domain": domain,
        "area_fraction": float(np.clip(area / (width * height), 0.0, 1.0)),
        "bubble_count": len(shapes),
    }


def collect_records(directory: Path, domain: str) -> list[dict[str, object]]:
    if not directory.is_dir():
        return []
    records = []
    for image_path in sorted(directory.rglob("*")):
        if image_path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if not image_path.with_suffix(".json").is_file():
            continue
        records.append(record_for_image(image_path, domain))
    return records


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def make_model(torch):
    import torch.nn as nn

    class BubbleAreaNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 32, 5, stride=2, padding=2),
                nn.BatchNorm2d(32),
                nn.GELU(),
                nn.Conv2d(32, 64, 3, stride=2, padding=1),
                nn.BatchNorm2d(64),
                nn.GELU(),
                nn.Conv2d(64, 128, 3, stride=2, padding=1),
                nn.BatchNorm2d(128),
                nn.GELU(),
                nn.Conv2d(128, 192, 3, stride=2, padding=1),
                nn.BatchNorm2d(192),
                nn.GELU(),
                nn.AdaptiveAvgPool2d(1),
            )
            self.head = nn.Sequential(
                nn.Flatten(),
                nn.Linear(192, 96),
                nn.GELU(),
                nn.Dropout(0.15),
                nn.Linear(96, 1),
            )

        def forward(self, x):
            return torch.sigmoid(self.head(self.features(x)).squeeze(1))

    return BubbleAreaNet()


def make_loader(torch, records, image_size: int, batch_size: int, shuffle: bool, num_workers: int, device, generator=None, image_cache=None):
    from torch.utils.data import DataLoader

    return DataLoader(
        BubbleDataset(records, image_size, image_cache),
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=num_workers,
        pin_memory=device.type == "cuda",
        persistent_workers=num_workers > 0,
    )


def predict(torch, model, records, args, device, image_cache=None) -> tuple[np.ndarray, np.ndarray]:
    if not records:
        return np.empty(0), np.empty(0)
    model.eval()
    loader = make_loader(torch, records, args.image_size, args.batch_size, False, args.num_workers, device, image_cache=image_cache)
    predictions: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    with torch.no_grad():
        for images, values in loader:
            predictions.append(model(images.to(device, non_blocking=True)).float().cpu().numpy())
            targets.append(values.numpy())
    return np.concatenate(targets), np.concatenate(predictions)


def metrics(target: np.ndarray, prediction: np.ndarray, baseline: float) -> dict[str, float | int]:
    if not len(target):
        return {"n": 0}
    error = prediction - target
    total = float(np.sum((target - target.mean()) ** 2))
    return {
        "n": int(len(target)),
        "baseline_mae_area_fraction": float(np.mean(np.abs(target - baseline))),
        "mae_area_fraction": float(np.mean(np.abs(error))),
        "rmse_area_fraction": float(np.sqrt(np.mean(error**2))),
        "r2": float(1.0 - np.sum(error**2) / total) if total > 0 else 0.0,
    }


def fit_one_seed(torch, train_records, evaluation_sets, args, seed: int, device) -> dict[str, object]:
    seed_everything(seed)
    shuffled = list(train_records)
    random.Random(seed).shuffle(shuffled)
    validation_count = max(1, int(round(len(shuffled) * args.validation_fraction)))
    validation = shuffled[:validation_count]
    fitting = shuffled[validation_count:]
    if not fitting:
        raise SystemExit("not enough training images after validation split")
    generator = torch.Generator().manual_seed(seed)
    image_cache: dict[Path, torch.Tensor] = {}
    train_loader = make_loader(torch, fitting, args.image_size, args.batch_size, True, args.num_workers, device, generator, image_cache)
    validation_loader = make_loader(torch, validation, args.image_size, args.batch_size, False, args.num_workers, device, image_cache=image_cache)
    model = make_model(torch).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    loss_fn = torch.nn.SmoothL1Loss(beta=0.01)
    amp_enabled = bool(args.amp and device.type == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)
    best_state = None
    best_validation = float("inf")
    best_epoch = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        for images, values in train_loader:
            images = images.to(device, non_blocking=True)
            values = values.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp_enabled):
                loss = loss_fn(model(images), values)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        model.eval()
        validation_loss = 0.0
        with torch.no_grad():
            for images, values in validation_loader:
                images = images.to(device, non_blocking=True)
                values = values.to(device, non_blocking=True)
                with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp_enabled):
                    validation_loss += float(loss_fn(model(images), values).float().cpu()) * len(values)
        validation_loss /= len(validation)
        if validation_loss < best_validation:
            best_validation = validation_loss
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
    if best_state is None:
        raise SystemExit("training produced no checkpoint")
    model.load_state_dict(best_state)
    baseline = float(np.mean([item["area_fraction"] for item in fitting]))
    result: dict[str, object] = {
        "seed": seed,
        "fit_count": len(fitting),
        "validation_count": len(validation),
        "best_epoch": best_epoch,
        "best_validation_smooth_l1": best_validation,
        "baseline_area_fraction": baseline,
        "evaluations": {},
    }
    for name, records in (("fit", fitting), ("validation", validation), *evaluation_sets.items()):
        target, prediction = predict(torch, model, records, args, device, image_cache)
        result["evaluations"][name] = metrics(target, prediction, baseline)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    args = parser.parse_args()
    import torch

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    device = torch.device("cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu")
    torch.set_float32_matmul_precision("high")
    base = args.data_root / "BoilingBench-5_Human_annotated_boiling_images"
    train_records = collect_records(base / "BubbleID_base" / "AnnotatedData" / "Classes-1" / "Train", "BubbleID_base_train")
    test_records = collect_records(base / "BubbleID_base" / "AnnotatedData" / "Classes-1" / "Test", "BubbleID_base_test")
    flow_records = collect_records(base / "BubbleID-Flow_fine-tuned_for_flow_boiling" / "AnnotatedData", "BubbleID_flow")
    facility_records = collect_records(base / "BubbleID_fine-tuned_for_new_facility" / "AnnotatedData", "BubbleID_new_facility")
    if not train_records or not test_records:
        raise SystemExit(f"BubbleID base Train/Test pairs not found: train={len(train_records)} test={len(test_records)}")
    evaluation_sets = {"base_test": test_records}
    if flow_records:
        evaluation_sets["flow_external"] = flow_records
    if facility_records:
        evaluation_sets["new_facility_external"] = facility_records
    runs = [fit_one_seed(torch, train_records, evaluation_sets, args, seed, device) for seed in args.seeds]
    result = {
        "experiment": "gpu_bubble_area_regression",
        "contract_schema_version": CONTRACT["schema_version"],
        "release": CONTRACT["release"],
        "hf_revision": CONTRACT["huggingface_revision"],
        "data_root_label": args.data_root.name,
        "split_policy": "BubbleID_base Train/Test are explicit; external domains are evaluation-only",
        "target": "polygon_bubble_area_fraction",
        "target_note": "Polygon areas are derived from public human annotations; the sigmoid head constrains predictions to [0, 1]. This is a visual boiling diagnostic, not a CHF label.",
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "model": "four-block convolutional regressor trained from scratch",
        "hyperparameters": {key: getattr(args, key) for key in ("epochs", "batch_size", "image_size", "learning_rate", "weight_decay", "validation_fraction", "num_workers", "amp")},
        "available_records": {"train": len(train_records), "base_test": len(test_records), "flow_external": len(flow_records), "new_facility_external": len(facility_records)},
        "runs": runs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"experiment": result["experiment"], "device": result["device"], "gpu_name": result["gpu_name"], "available_records": result["available_records"], "runs": [{"seed": run["seed"], "base_test": run["evaluations"]["base_test"]} for run in runs]}, indent=2))


if __name__ == "__main__":
    main()

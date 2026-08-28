#!/usr/bin/env python3
"""Download the pinned, small processed BoilingBench current-data bundle.

Raw videos, LVM/DTA files, and multi-gigabyte waveform arrays are intentionally
not downloaded by this helper. Run audit_current_data.py after downloading.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "baselines" / "chfwatch" / "data_contract.json"


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+", default=["BB-1", "BB-2", "BB-3", "BB-4"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    contract = json.loads(CONTRACT.read_text())
    revision = contract["huggingface_revision"]
    dataset_map = contract["datasets"]
    for dataset in args.datasets:
        if dataset not in dataset_map:
            parser.error(f"unknown dataset {dataset}; choose from {sorted(dataset_map)}")
        source_dir = dataset_map[dataset]["directory"]
        names = list(contract["required_processed_files"])
        if dataset_map[dataset]["microphone_band_power"]:
            names.append("microphone_band_integrated_power.csv")
        if dataset_map[dataset]["continuous_ae_waveform"]:
            names.extend(("ae_wfs_band_integrated_power.csv", "ae_wfs_channel_1_metadata.json"))
        for name in names:
            target = args.data_root / dataset / name
            if target.exists() and not args.force:
                continue
            url = f"https://huggingface.co/datasets/{contract['huggingface_dataset']}/resolve/{revision}/{source_dir}/{name}"
            print(f"Downloading {dataset}/{name}")
            download(url, target)


if __name__ == "__main__":
    main()

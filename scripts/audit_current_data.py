#!/usr/bin/env python3
"""Audit a local copy of the current public BoilingBench processed exports.

The audit records provenance, file checksums, schema, timing, modality
availability, and label status without copying raw data into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = json.loads((ROOT / "baselines" / "chfwatch" / "data_contract.json").read_text())
HF_REVISION = CONTRACT["huggingface_revision"]
DATASETS = tuple(CONTRACT["datasets"])
REQUIRED = tuple(CONTRACT["required_processed_files"])
OPTIONAL = tuple(CONTRACT["optional_processed_files"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_case(root: Path, dataset: str) -> dict[str, object]:
    case_dir = root / dataset
    errors: list[str] = []
    warnings: list[str] = []
    files: dict[str, object] = {}
    for name in (*REQUIRED, *OPTIONAL):
        path = case_dir / name
        if path.exists():
            files[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        elif name in REQUIRED:
            errors.append(f"missing required file: {name}")

    summary: dict[str, object] = {}
    if (case_dir / "summary.json").exists():
        try:
            summary = json.loads((case_dir / "summary.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid summary.json: {exc}")

    arrays: dict[str, object] = {}
    if (case_dir / "thermal_timeseries.npz").exists():
        try:
            with np.load(case_dir / "thermal_timeseries.npz", allow_pickle=False) as data:
                keys = list(data.files)
                lengths = {key: int(np.asarray(data[key]).shape[0]) for key in keys}
                arrays = {"keys": keys, "lengths": lengths}
                if len(set(lengths.values())) != 1:
                    errors.append("thermal NPZ arrays have inconsistent lengths")
                time = np.asarray(data["time_reference_temperature_s"], dtype=float)
                if len(time) < 2 or not np.all(np.isfinite(time)):
                    errors.append("thermal reference clock is missing or non-finite")
                elif np.any(np.diff(time) <= 0):
                    errors.append("thermal reference clock is not strictly increasing")
                else:
                    arrays["samples"] = int(len(time))
                    arrays["duration_s"] = float(time[-1] - time[0])
                    arrays["median_dt_s"] = float(np.median(np.diff(time)))
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f"could not inspect thermal NPZ: {exc}")

    csvs: dict[str, object] = {}
    for name in ("critical_events.csv", "ae_hit_parameters_aligned.csv", "hydrophone_band_integrated_power.csv", "microphone_band_integrated_power.csv", "ae_wfs_band_integrated_power.csv"):
        path = case_dir / name
        if not path.exists():
            continue
        try:
            frame = pd.read_csv(path)
            csvs[name] = {"rows": int(len(frame)), "columns": list(frame.columns)}
        except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            errors.append(f"could not read {name}: {exc}")

    events: list[dict[str, object]] = []
    event_path = case_dir / "critical_events.csv"
    if event_path.exists():
        event_frame = pd.read_csv(event_path)
        events = event_frame.to_dict("records")
        proxy = event_frame[event_frame["event_name"].eq("chf_proxy")]
        if proxy.empty:
            warnings.append("no chf_proxy event is present")
        elif not proxy["evidence_status"].eq("not_confirmed").all():
            errors.append("chf_proxy is not consistently marked not_confirmed")
        if event_frame["event_name"].eq("confirmed_chf").any():
            errors.append("confirmed_chf event must not be inferred from current release")

    available = {
        "thermal": (case_dir / "thermal_timeseries.npz").exists(),
        "hydrophone": (case_dir / "hydrophone_band_integrated_power.csv").exists(),
        "microphone": (case_dir / "microphone_band_integrated_power.csv").exists(),
        "ae_hits": (case_dir / "ae_hit_parameters_aligned.csv").exists(),
        "continuous_ae_waveform": (
            (case_dir / "ae_wfs_band_integrated_power.csv").exists()
            or (case_dir / "ae_wfs_channel_1_metadata.json").exists()
        ),
    }
    if not available["microphone"]:
        warnings.append("microphone band-power export is absent")
    if available["continuous_ae_waveform"]:
        warnings.append("continuous AE is represented by processed band-power; raw waveform arrays are not audited")
    else:
        warnings.append("continuous AE waveform feature export is absent from this case")
    expected = CONTRACT["datasets"][dataset]
    if available["microphone"] != expected["microphone_band_power"]:
        errors.append("observed microphone availability does not match the data contract")
    if available["continuous_ae_waveform"] != expected["continuous_ae_waveform"]:
        errors.append("observed continuous-AE availability does not match the data contract")
    warnings.append("processed heat flux and chf_proxy are not confirmed CHF labels")
    return {
        "dataset": dataset,
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "files": files,
        "arrays": arrays,
        "csvs": csvs,
        "events": events,
        "modalities": available,
        "summary_fields": {key: summary.get(key) for key in ("test_id", "analysis_mode", "duration_s", "chf_event_status", "max_heat_flux_W_cm2")},
    }


def markdown(report: dict[str, object]) -> str:
    cases = report["cases"]
    lines = [
        "# BoilingBench current-release audit",
        "",
        f"- Contract schema: `{CONTRACT['schema_version']}`",
        f"- Release: `{CONTRACT['release']}`",
        f"- Hugging Face revision: `{report['hf_revision']}`",
        f"- Generated: `{report['generated_utc']}`",
        "- Scope: public processed exports; no raw files copied into this repository",
        "",
        "| Dataset | Status | Duration (s) | Samples | Hydrophone | Microphone | AE hits | Continuous AE | CHF status |",
        "|---|---|---:|---:|---|---|---|---|---|",
    ]
    for case in cases:
        fields = case.get("summary_fields", {})
        arrays = case.get("arrays", {})
        modalities = case.get("modalities", {})
        lines.append(
            f"| {case['dataset']} | {case['status']} | {fields.get('duration_s', arrays.get('duration_s', ''))} | {arrays.get('samples', '')} | "
            f"{modalities.get('hydrophone')} | {modalities.get('microphone')} | {modalities.get('ae_hits')} | {modalities.get('continuous_ae_waveform')} | {fields.get('chf_event_status', 'not recorded')} |"
        )
    lines += ["", "## Interpretation", "", "The current package supports cross-dataset heat-flux regression and modality-availability audits. It does not support a confirmed-CHF alarm benchmark: `chf_proxy` is marked `not_confirmed`. The processed target is an analysis product derived from the thermal data, so thermal-regression metrics are not independent physical validation.", "", "## Warnings", ""]
    for case in cases:
        for warning in case.get("warnings", []):
            lines.append(f"- {case['dataset']}: {warning}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="JSON output path")
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = {
        "contract_schema_version": CONTRACT["schema_version"],
        "release": CONTRACT["release"],
        "hf_revision": HF_REVISION,
        "target": CONTRACT["target"],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cases": [audit_case(args.data_root, dataset) for dataset in DATASETS],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(report))
    print(json.dumps(report, indent=2))
    if any(case["status"] == "fail" for case in report["cases"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

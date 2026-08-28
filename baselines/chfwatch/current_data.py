"""Loader for the public processed BoilingBench-1/2/3/4 v0.1.0 exports.

The current release exposes one processed run per dataset. This adapter does
not fabricate five-surface splits or treat chf_proxy as confirmed CHF.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

CONTRACT = json.loads((Path(__file__).resolve().parent / "data_contract.json").read_text())
HF_REVISION = CONTRACT["huggingface_revision"]
BIN_S = 1.36
THERMAL_FEATURES = (
    "surface_temperature_C", "wall_superheat_C", "tc_spread_C", "thermal_fit_R2",
)
HYDROPHONE_FEATURES = ("hydrophone_db",)
MICROPHONE_FEATURES = ("microphone_db",)
AE_FEATURES = ("ae_hits",)
AE_WAVEFORM_FEATURES = ("ae_waveform_db",)
COMMON_FEATURES = THERMAL_FEATURES + HYDROPHONE_FEATURES + AE_FEATURES
ALL_FEATURES = COMMON_FEATURES + AE_WAVEFORM_FEATURES + MICROPHONE_FEATURES
# Backward-compatible default: microphone is not present in BB-1/BB-2.
FEATURES = COMMON_FEATURES


def _interpolate(path: Path, time_col: str, value_col: str, times: np.ndarray) -> np.ndarray:
    source = pd.read_csv(path).dropna(subset=[time_col, value_col]).sort_values(time_col)
    if len(source) < 2:
        return np.full(times.shape, np.nan)
    return np.interp(times, source[time_col].to_numpy(float), source[value_col].to_numpy(float), left=np.nan, right=np.nan)


def load_processed_case(
    case_dir: str | Path,
    required_features: tuple[str, ...] | None = None,
    bin_s: float = BIN_S,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return aligned feature windows and marker provenance.

    ``required_features`` controls missing-modality handling. It defaults to
    features shared by all four current public cases; requesting microphone
    features makes BB-1/BB-2 ineligible rather than silently imputing them.
    """
    case_dir = Path(case_dir)
    required_features = required_features or COMMON_FEATURES
    with np.load(case_dir / "thermal_timeseries.npz", allow_pickle=False) as arrays:
        time_s = arrays["time_reference_temperature_s"].astype(float)
        edges = np.arange(0, float(time_s[-1]) + bin_s, bin_s)
        bins = np.clip(np.digitize(time_s, edges) - 1, 0, len(edges) - 2)
        centers = (edges[:-1] + edges[1:]) / 2

        def mean(key: str) -> np.ndarray:
            values = arrays[key].astype(float)
            return np.array([np.nanmean(values[bins == index]) if np.any(bins == index) else np.nan for index in range(len(centers))])

        frame = pd.DataFrame({
            "time_s": centers,
            "surface_temperature_C": mean("surface_temperature_C"),
            "wall_superheat_C": mean("wall_superheat_C"),
            "thermal_fit_R2": mean("linear_temperature_fit_R2"),
            "heat_flux_W_cm2": mean("heat_flux_W_cm2"),
        })
        thermocouples = np.vstack([arrays[f"thermocouple_{index}_C"] for index in range(1, 5)])
        frame["tc_spread_C"] = np.array([
            np.nanmean(np.nanstd(thermocouples[:, bins == index], axis=0)) if np.any(bins == index) else np.nan
            for index in range(len(centers))
        ])

    hydrophone_path = case_dir / "hydrophone_band_integrated_power.csv"
    microphone_path = case_dir / "microphone_band_integrated_power.csv"
    ae_waveform_path = case_dir / "ae_wfs_band_integrated_power.csv"
    frame["hydrophone_db"] = _interpolate(hydrophone_path, "Time (s)", "Band-integrated hydrophone power proxy (dB re V^2)", centers) if hydrophone_path.exists() else np.nan
    frame["microphone_db"] = _interpolate(microphone_path, "Time (s)", "Band-integrated microphone power proxy (dB re V^2)", centers) if microphone_path.exists() else np.nan
    frame["ae_waveform_db"] = _interpolate(ae_waveform_path, "Time (s)", "Band-integrated AE waveform power proxy (dB re V^2)", centers) if ae_waveform_path.exists() else np.nan
    hits = pd.read_csv(case_dir / "ae_hit_parameters_aligned.csv")
    hit_time = pd.to_numeric(hits["AE_Hit_Time"], errors="coerce").dropna().to_numpy(float)
    frame["ae_hits"] = np.histogram(hit_time, bins=edges)[0].astype(float)
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[*required_features, "heat_flux_W_cm2"]).reset_index(drop=True)

    events = pd.read_csv(case_dir / "critical_events.csv")
    proxy = events.loc[events["event_name"].eq("chf_proxy"), "time_reference_temperature_s"]
    return frame, {
        "hf_revision": HF_REVISION,
        "chf_event_status": "not_confirmed",
        "screening_chf_proxy_time_s": float(proxy.iloc[0]) if len(proxy) else None,
        "continuous_ae_waveform": (
            ae_waveform_path.exists()
            or (case_dir / "ae_wfs_channel_1_metadata.json").exists()
        ),
        "continuous_ae_waveform_product": ae_waveform_path.exists(),
        "available_modalities": {
            "thermal": True,
            "hydrophone": hydrophone_path.exists(),
            "microphone": microphone_path.exists(),
            "ae_hits": (case_dir / "ae_hit_parameters_aligned.csv").exists(),
            "ae_waveform_processed": ae_waveform_path.exists(),
        },
        "required_features": list(required_features),
        "bin_s": bin_s,
    }

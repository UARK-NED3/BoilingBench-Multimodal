"""Loader for the public processed BoilingBench-3/4 v0.1.0 exports.

The current release exposes one processed run per dataset. This adapter does
not fabricate five-surface splits or treat chf_proxy as confirmed CHF.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HF_REVISION = "e4d977db425e5a283c5f26b13b452a84868a5c5a"
BIN_S = 1.36
FEATURES = (
    "surface_temperature_C", "wall_superheat_C", "tc_spread_C",
    "thermal_fit_R2", "hydrophone_db", "microphone_db", "ae_hits",
)


def _interpolate(path: Path, time_col: str, value_col: str, times: np.ndarray) -> np.ndarray:
    source = pd.read_csv(path).dropna(subset=[time_col, value_col]).sort_values(time_col)
    if len(source) < 2:
        return np.full(times.shape, np.nan)
    return np.interp(times, source[time_col].to_numpy(float), source[value_col].to_numpy(float), left=np.nan, right=np.nan)


def load_processed_case(case_dir: str | Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return fixed-width, aligned feature windows and marker provenance."""
    case_dir = Path(case_dir)
    with np.load(case_dir / "thermal_timeseries.npz", allow_pickle=False) as arrays:
        time_s = arrays["time_reference_temperature_s"].astype(float)
        edges = np.arange(0, float(time_s[-1]) + BIN_S, BIN_S)
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

    frame["hydrophone_db"] = _interpolate(case_dir / "hydrophone_band_integrated_power.csv", "Time (s)", "Band-integrated hydrophone power proxy (dB re V^2)", centers)
    frame["microphone_db"] = _interpolate(case_dir / "microphone_band_integrated_power.csv", "Time (s)", "Band-integrated microphone power proxy (dB re V^2)", centers)
    hits = pd.read_csv(case_dir / "ae_hit_parameters_aligned.csv")
    hit_time = pd.to_numeric(hits["AE_Hit_Time"], errors="coerce").dropna().to_numpy(float)
    frame["ae_hits"] = np.histogram(hit_time, bins=edges)[0].astype(float)
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[*FEATURES, "heat_flux_W_cm2"]).reset_index(drop=True)

    events = pd.read_csv(case_dir / "critical_events.csv")
    proxy = events.loc[events["event_name"].eq("chf_proxy"), "time_reference_temperature_s"]
    return frame, {
        "hf_revision": HF_REVISION,
        "chf_event_status": "not_confirmed",
        "screening_chf_proxy_time_s": float(proxy.iloc[0]) if len(proxy) else None,
        "continuous_ae_waveform": False,
    }

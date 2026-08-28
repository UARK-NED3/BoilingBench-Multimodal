from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "baselines" / "chfwatch"))
from current_data import COMMON_FEATURES, FEATURES, HF_REVISION, load_processed_case  # noqa: E402


def _write_case(root: Path, include_microphone: bool = True, include_waveform: bool = True) -> None:
    time = np.arange(0.0, 4.0, 0.2)
    np.savez(
        root / "thermal_timeseries.npz",
        time_reference_temperature_s=time,
        surface_temperature_C=100 + time,
        wall_superheat_C=2 + time / 10,
        linear_temperature_fit_R2=np.full_like(time, 0.99),
        heat_flux_W_cm2=20 + time,
        thermocouple_1_C=90 + time,
        thermocouple_2_C=91 + time,
        thermocouple_3_C=92 + time,
        thermocouple_4_C=93 + time,
    )
    pd.DataFrame({"Time (s)": [0, 2, 4], "Band-integrated hydrophone power proxy (dB re V^2)": [1, 2, 3]}).to_csv(root / "hydrophone_band_integrated_power.csv", index=False)
    if include_microphone:
        pd.DataFrame({"Time (s)": [0, 2, 4], "Band-integrated microphone power proxy (dB re V^2)": [4, 5, 6]}).to_csv(root / "microphone_band_integrated_power.csv", index=False)
    if include_waveform:
        pd.DataFrame({"Time (s)": [0, 2, 4], "Band-integrated AE waveform power proxy (dB re V^2)": [7, 8, 9]}).to_csv(root / "ae_wfs_band_integrated_power.csv", index=False)
    pd.DataFrame({"AE_Hit_Time": [0.3, 1.4, 2.2]}).to_csv(root / "ae_hit_parameters_aligned.csv", index=False)
    pd.DataFrame({"event_name": ["chf_proxy"], "time_reference_temperature_s": [2.4]}).to_csv(root / "critical_events.csv", index=False)


def test_loader_marks_proxy_as_unconfirmed_and_exposes_only_current_features(tmp_path: Path) -> None:
    _write_case(tmp_path)
    frame, metadata = load_processed_case(tmp_path)
    assert not frame.empty
    assert set(FEATURES).issubset(frame.columns)
    assert metadata["hf_revision"] == HF_REVISION
    assert metadata["chf_event_status"] == "not_confirmed"
    assert metadata["continuous_ae_waveform"] is True
    assert metadata["continuous_ae_waveform_product"] is True
    assert metadata["screening_chf_proxy_time_s"] == 2.4


def test_missing_microphone_does_not_drop_common_modality_rows(tmp_path: Path) -> None:
    _write_case(tmp_path, include_microphone=False, include_waveform=False)
    frame, metadata = load_processed_case(tmp_path, required_features=COMMON_FEATURES)
    assert len(frame) > 0
    assert metadata["available_modalities"]["microphone"] is False
    assert metadata["required_features"] == list(COMMON_FEATURES)


def test_time_is_available_as_an_explicit_baseline_feature(tmp_path: Path) -> None:
    _write_case(tmp_path)
    frame, _metadata = load_processed_case(tmp_path, required_features=("time_s",))
    assert frame["time_s"].is_monotonic_increasing
    assert frame["time_s"].notna().all()

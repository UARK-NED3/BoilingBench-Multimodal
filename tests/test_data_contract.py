from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1] / "baselines" / "chfwatch" / "data_contract.json"


def test_current_data_contract_is_pinned_and_explicit() -> None:
    contract = json.loads(CONTRACT.read_text())
    assert contract["benchmark"] == "BoilingBench-Multimodal"
    assert contract["release"] == "v0.1.0"
    assert contract["huggingface_revision"] == "e4d977db425e5a283c5f26b13b452a84868a5c5a"
    assert set(contract["datasets"]) == {"BB-1", "BB-2", "BB-3", "BB-4"}
    assert contract["target"]["independent_physical_measurement"] is False
    assert contract["target"]["use_as_confirmed_chf_label"] is False
    assert contract["split_policy"]["primary_group"] == "dataset_id"
    assert contract["split_policy"]["adjacent_windows_may_cross_splits"] is False


def test_contract_download_scope_excludes_raw_exports() -> None:
    contract = json.loads(CONTRACT.read_text())
    files = contract["required_processed_files"] + contract["optional_processed_files"]
    assert all(not name.endswith((".mp4", ".npy", ".lvm", ".dta")) for name in files)
    assert "thermal_timeseries.npz" in contract["required_processed_files"]
    assert "ae_wfs_band_integrated_power.csv" in contract["optional_processed_files"]


def test_contract_declares_the_release_modality_matrix() -> None:
    contract = json.loads(CONTRACT.read_text())
    assert contract["datasets"]["BB-1"]["continuous_ae_waveform"] is True
    assert contract["datasets"]["BB-2"]["continuous_ae_waveform"] is True
    assert contract["datasets"]["BB-3"]["continuous_ae_waveform"] is False
    assert contract["datasets"]["BB-4"]["continuous_ae_waveform"] is False
    assert contract["datasets"]["BB-1"]["microphone_band_power"] is False
    assert contract["datasets"]["BB-3"]["microphone_band_power"] is True


def test_contract_is_the_loader_revision_source() -> None:
    import sys

    sys.path.insert(0, str(CONTRACT.parent))
    from current_data import CONTRACT as LOADER_CONTRACT, HF_REVISION  # noqa: E402

    contract_revision = json.loads(CONTRACT.read_text())["huggingface_revision"]
    assert LOADER_CONTRACT["huggingface_revision"] == contract_revision
    assert HF_REVISION == contract_revision

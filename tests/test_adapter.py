"""Tests for the CHF-Watch reference baseline adapter (splits -> surfaces)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "baselines" / "chfwatch"))

import adapter  # noqa: E402

MANIFEST = REPO / "MANIFEST_NED3_007_FILES.csv"
SPLITS = REPO / "splits"


def _split_files() -> list[Path]:
    return sorted(SPLITS.glob("ned3-007-lso-surface-*.csv"))


def test_manifest_maps_all_five_surfaces() -> None:
    r2s = adapter.run_to_surface_map(MANIFEST)
    assert set(r2s.values()) == set(adapter.SURFACES)
    assert len(r2s) >= 10  # 5 surfaces x >=2 runs each per the manifest


@pytest.mark.parametrize("split_csv", [str(p) for p in _split_files()], ids=lambda s: Path(s).stem)
def test_each_split_holds_out_exactly_one_surface(split_csv: str) -> None:
    train, test = adapter.load_surface_split(split_csv, MANIFEST)
    assert len(test) == 1
    assert test[0] in adapter.SURFACES
    assert set(train) == set(adapter.SURFACES) - set(test)
    assert test[0] in split_csv  # file names are per-surface


def test_test_runs_are_only_held_out_surface() -> None:
    r2s = adapter.run_to_surface_map(MANIFEST)
    for split_csv in _split_files():
        train, test = adapter.load_surface_split(split_csv, MANIFEST)
        assert test[0] == r2s[next(r for r in r2s if r2s[r] == test[0])]


def test_unknown_run_id_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("dataset_id,run_id,split,task,notes\nned3-007,B999,test,multimodal_fusion,\n")
    with pytest.raises(ValueError, match="B999"):
        adapter.load_surface_split(bad, MANIFEST)


def test_published_labels_cover_all_surfaces_and_flag_inferred() -> None:
    labels = adapter.load_published_chf_labels()
    inferred = adapter.inferred_chf_surfaces()
    assert set(labels) == set(adapter.SURFACES)
    assert labels["microchannel"] > 0
    assert inferred == ["microchannel"]
    assert labels["polished_cu"] < labels["cu_foam_pH0"]  # smooth Cu is the low-CHF case
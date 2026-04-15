"""Tests for driftwatch.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.snapshot import (
    SnapshotError,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


SAMPLE_CONFIG = {"database": {"host": "localhost", "port": 5432}, "debug": False}


# ---------------------------------------------------------------------------
# save_snapshot
# ---------------------------------------------------------------------------


def test_save_snapshot_creates_file(snap_dir: Path) -> None:
    path = save_snapshot(SAMPLE_CONFIG, "prod", directory=snap_dir)
    assert path.exists()
    assert path.suffix == ".json"


def test_save_snapshot_stores_config(snap_dir: Path) -> None:
    save_snapshot(SAMPLE_CONFIG, "prod", directory=snap_dir)
    raw = json.loads((snap_dir / "prod.json").read_text())
    assert raw["config"] == SAMPLE_CONFIG


def test_save_snapshot_records_name(snap_dir: Path) -> None:
    save_snapshot(SAMPLE_CONFIG, "staging", directory=snap_dir)
    raw = json.loads((snap_dir / "staging.json").read_text())
    assert raw["name"] == "staging"


def test_save_snapshot_creates_directory(snap_dir: Path) -> None:
    assert not snap_dir.exists()
    save_snapshot(SAMPLE_CONFIG, "dev", directory=snap_dir)
    assert snap_dir.is_dir()


# ---------------------------------------------------------------------------
# load_snapshot
# ---------------------------------------------------------------------------


def test_load_snapshot_returns_config(snap_dir: Path) -> None:
    save_snapshot(SAMPLE_CONFIG, "prod", directory=snap_dir)
    loaded = load_snapshot("prod", directory=snap_dir)
    assert loaded == SAMPLE_CONFIG


def test_load_snapshot_missing_raises(snap_dir: Path) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot("nonexistent", directory=snap_dir)


def test_load_snapshot_corrupt_json_raises(snap_dir: Path) -> None:
    snap_dir.mkdir(parents=True)
    (snap_dir / "bad.json").write_text("not-json", encoding="utf-8")
    with pytest.raises(SnapshotError, match="Could not read"):
        load_snapshot("bad", directory=snap_dir)


# ---------------------------------------------------------------------------
# list_snapshots
# ---------------------------------------------------------------------------


def test_list_snapshots_empty_when_no_directory(snap_dir: Path) -> None:
    assert list_snapshots(directory=snap_dir) == []


def test_list_snapshots_returns_names(snap_dir: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        save_snapshot(SAMPLE_CONFIG, name, directory=snap_dir)
    assert list_snapshots(directory=snap_dir) == ["alpha", "beta", "gamma"]


def test_list_snapshots_sorted(snap_dir: Path) -> None:
    for name in ("zebra", "apple", "mango"):
        save_snapshot(SAMPLE_CONFIG, name, directory=snap_dir)
    names = list_snapshots(directory=snap_dir)
    assert names == sorted(names)

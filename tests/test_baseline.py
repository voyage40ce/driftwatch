"""Tests for driftwatch/baseline.py."""

from __future__ import annotations

import json

import pytest

from driftwatch.baseline import (
    BaselineError,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)


@pytest.fixture(autouse=True)
def isolated_baseline_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIFTWATCH_BASELINE_DIR", str(tmp_path / "baselines"))


SAMPLE = {"app": {"port": 8080, "debug": False}}


def test_save_baseline_creates_file():
    path = save_baseline("production", SAMPLE)
    assert path.exists()


def test_save_baseline_stores_config():
    save_baseline("production", SAMPLE)
    assert load_baseline("production") == SAMPLE


def test_save_baseline_records_name():
    path = save_baseline("staging", SAMPLE)
    payload = json.loads(path.read_text())
    assert payload["name"] == "staging"


def test_save_baseline_records_timestamp():
    path = save_baseline("staging", SAMPLE)
    payload = json.loads(path.read_text())
    assert "saved_at" in payload


def test_load_baseline_missing_raises():
    with pytest.raises(BaselineError, match="not found"):
        load_baseline("nonexistent")


def test_load_baseline_corrupt_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIFTWATCH_BASELINE_DIR", str(tmp_path / "baselines"))
    path = save_baseline("bad", SAMPLE)
    path.write_text("not valid json")
    with pytest.raises(BaselineError, match="corrupt"):
        load_baseline("bad")


def test_list_baselines_empty():
    assert list_baselines() == []


def test_list_baselines_returns_names():
    save_baseline("alpha", SAMPLE)
    save_baseline("beta", SAMPLE)
    assert list_baselines() == ["alpha", "beta"]


def test_delete_baseline_removes_file():
    save_baseline("temp", SAMPLE)
    delete_baseline("temp")
    assert "temp" not in list_baselines()


def test_delete_baseline_missing_raises():
    with pytest.raises(BaselineError, match="not found"):
        delete_baseline("ghost")


def test_overwrite_baseline_updates_config():
    save_baseline("prod", SAMPLE)
    updated = {"app": {"port": 9090, "debug": True}}
    save_baseline("prod", updated)
    assert load_baseline("prod") == updated

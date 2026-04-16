"""Tests for driftwatch.diffstore."""
import pytest
from pathlib import Path
from driftwatch.diffstore import record_diff, load_diffs, clear_diffs, StoredDiff
from driftwatch.differ import DriftReport, DriftChange


@pytest.fixture
def store_dir(tmp_path):
    return tmp_path / "diffstore"


def _clean_report():
    return DriftReport(has_drift=False, changes=[])


def _drift_report():
    return DriftReport(
        has_drift=True,
        changes=[DriftChange(key="db.host", source_value="localhost", deployed_value="prod-db")],
    )


def test_record_diff_creates_file(store_dir):
    record_diff(_clean_report(), "staging", base_dir=store_dir)
    assert (store_dir / "staging.jsonl").exists()


def test_record_diff_returns_stored_diff(store_dir):
    entry = record_diff(_clean_report(), "staging", base_dir=store_dir)
    assert isinstance(entry, StoredDiff)
    assert entry.env == "staging"
    assert entry.has_drift is False


def test_record_diff_with_drift(store_dir):
    entry = record_diff(_drift_report(), "prod", base_dir=store_dir)
    assert entry.has_drift is True
    assert len(entry.changes) == 1
    assert entry.changes[0]["key"] == "db.host"


def test_load_diffs_returns_entries(store_dir):
    record_diff(_clean_report(), "staging", base_dir=store_dir)
    record_diff(_drift_report(), "staging", base_dir=store_dir)
    results = load_diffs("staging", base_dir=store_dir)
    assert len(results) == 2


def test_load_diffs_missing_env_returns_empty(store_dir):
    results = load_diffs("nonexistent", base_dir=store_dir)
    assert results == []


def test_load_diffs_respects_limit(store_dir):
    for _ in range(5):
        record_diff(_clean_report(), "staging", base_dir=store_dir)
    results = load_diffs("staging", limit=3, base_dir=store_dir)
    assert len(results) == 3


def test_clear_diffs_returns_count(store_dir):
    record_diff(_clean_report(), "staging", base_dir=store_dir)
    record_diff(_drift_report(), "staging", base_dir=store_dir)
    count = clear_diffs("staging", base_dir=store_dir)
    assert count == 2


def test_clear_diffs_removes_file(store_dir):
    record_diff(_clean_report(), "staging", base_dir=store_dir)
    clear_diffs("staging", base_dir=store_dir)
    assert not (store_dir / "staging.jsonl").exists()


def test_clear_diffs_missing_env_returns_zero(store_dir):
    assert clear_diffs("ghost", base_dir=store_dir) == 0

"""Tests for driftwatch.archiver."""
import pytest
from driftwatch.archiver import (
    archive_report, load_archives, clear_archives, ArchivedReport, ArchiverError
)
from driftwatch.differ import DriftReport
from driftwatch.differ import DriftReport
from dataclasses import dataclass
from typing import List


# Minimal DriftReport-compatible stubs
@dataclass
class _Change:
    key: str
    source: object
    deployed: object
    kind: str


def _clean_report():
    return DriftReport(has_drift=False, changes=[])


def _drift_report():
    from driftwatch.differ import DriftReport
    c = _Change(key="db.host", source="prod", deployed="staging", kind="changed")
    return DriftReport(has_drift=True, changes=[c])


@pytest.fixture
def arc_dir(tmp_path):
    return str(tmp_path / "archives")


def test_archive_creates_file(arc_dir):
    r = archive_report(_clean_report(), env="prod", base=arc_dir)
    import os
    assert os.path.exists(r.path)


def test_archive_stores_env(arc_dir):
    r = archive_report(_clean_report(), env="staging", base=arc_dir)
    assert r.env == "staging"


def test_archive_no_drift(arc_dir):
    r = archive_report(_clean_report(), env="prod", base=arc_dir)
    assert r.has_drift is False
    assert r.changes == []


def test_archive_with_drift(arc_dir):
    r = archive_report(_drift_report(), env="prod", base=arc_dir)
    assert r.has_drift is True
    assert len(r.changes) == 1
    assert r.changes[0]["key"] == "db.host"


def test_load_archives_empty_dir(arc_dir):
    entries = load_archives(base=arc_dir)
    assert entries == []


def test_load_archives_returns_saved(arc_dir):
    archive_report(_clean_report(), env="prod", base=arc_dir)
    archive_report(_drift_report(), env="prod", base=arc_dir)
    entries = load_archives(base=arc_dir)
    assert len(entries) == 2


def test_load_archives_filters_by_env(arc_dir):
    archive_report(_clean_report(), env="prod", base=arc_dir)
    archive_report(_drift_report(), env="staging", base=arc_dir)
    entries = load_archives(env="prod", base=arc_dir)
    assert all(e.env == "prod" for e in entries)
    assert len(entries) == 1


def test_clear_archives_removes_all(arc_dir):
    archive_report(_clean_report(), env="prod", base=arc_dir)
    archive_report(_clean_report(), env="prod", base=arc_dir)
    removed = clear_archives(base=arc_dir)
    assert removed == 2
    assert load_archives(base=arc_dir) == []


def test_clear_archives_filters_by_env(arc_dir):
    archive_report(_clean_report(), env="prod", base=arc_dir)
    archive_report(_clean_report(), env="staging", base=arc_dir)
    removed = clear_archives(env="prod", base=arc_dir)
    assert removed == 1
    remaining = load_archives(base=arc_dir)
    assert all(e.env == "staging" for e in remaining)

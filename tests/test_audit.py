"""Tests for driftwatch.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.audit import AuditEntry, AuditError, load_entries, record
from driftwatch.differ import DriftReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_report() -> DriftReport:
    return DriftReport(changed={}, added={}, removed={})


def _drift_report() -> DriftReport:
    return DriftReport(
        changed={"db.host": ("old", "new")},
        added={"feature.flag": True},
        removed={"legacy.key": "val"},
    )


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------

def test_record_creates_log_file(tmp_path):
    audit_dir = str(tmp_path / "audit")
    record(_clean_report(), "source.yaml", "deployed.yaml", audit_dir=audit_dir)
    assert (Path(audit_dir) / "drift_audit.jsonl").exists()


def test_record_returns_audit_entry(tmp_path):
    audit_dir = str(tmp_path / "audit")
    entry = record(_clean_report(), "s.yaml", "d.yaml", audit_dir=audit_dir)
    assert isinstance(entry, AuditEntry)


def test_record_no_drift_entry(tmp_path):
    audit_dir = str(tmp_path / "audit")
    entry = record(_clean_report(), "s.yaml", "d.yaml", audit_dir=audit_dir)
    assert entry.has_drift is False
    assert entry.changed == []
    assert entry.added == []
    assert entry.removed == []


def test_record_drift_entry_captures_keys(tmp_path):
    audit_dir = str(tmp_path / "audit")
    entry = record(_drift_report(), "s.yaml", "d.yaml", audit_dir=audit_dir)
    assert entry.has_drift is True
    assert "db.host" in entry.changed
    assert "feature.flag" in entry.added
    assert "legacy.key" in entry.removed


def test_record_stores_label(tmp_path):
    audit_dir = str(tmp_path / "audit")
    entry = record(_clean_report(), "s.yaml", "d.yaml", label="prod", audit_dir=audit_dir)
    assert entry.label == "prod"


def test_record_appends_multiple_entries(tmp_path):
    audit_dir = str(tmp_path / "audit")
    record(_clean_report(), "s.yaml", "d.yaml", audit_dir=audit_dir)
    record(_drift_report(), "s.yaml", "d.yaml", audit_dir=audit_dir)
    entries = load_entries(audit_dir=audit_dir)
    assert len(entries) == 2


def test_record_writes_valid_jsonl(tmp_path):
    audit_dir = str(tmp_path / "audit")
    record(_drift_report(), "s.yaml", "d.yaml", audit_dir=audit_dir)
    log_file = Path(audit_dir) / "drift_audit.jsonl"
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert "timestamp" in data
    assert data["has_drift"] is True


# ---------------------------------------------------------------------------
# load_entries()
# ---------------------------------------------------------------------------

def test_load_entries_empty_when_no_file(tmp_path):
    entries = load_entries(audit_dir=str(tmp_path / "nonexistent"))
    assert entries == []


def test_load_entries_round_trip(tmp_path):
    audit_dir = str(tmp_path / "audit")
    record(_drift_report(), "source.yaml", "deployed.yaml", label="staging", audit_dir=audit_dir)
    entries = load_entries(audit_dir=audit_dir)
    assert len(entries) == 1
    e = entries[0]
    assert e.source_file == "source.yaml"
    assert e.deployed_file == "deployed.yaml"
    assert e.label == "staging"
    assert e.has_drift is True


def test_load_entries_raises_on_corrupt_jsonl(tmp_path):
    audit_dir = str(tmp_path / "audit")
    log_file = Path(audit_dir) / "drift_audit.jsonl"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("not-valid-json\n")
    with pytest.raises(AuditError):
        load_entries(audit_dir=audit_dir)

"""Tests for driftwatch.exporter."""

from __future__ import annotations

import json

import pytest

from driftwatch.differ import DriftReport
from driftwatch.exporter import ExportError, ExportOptions, export_report


def _clean_report() -> DriftReport:
    return DriftReport(changed={}, added={}, removed={})


def _drift_report() -> DriftReport:
    return DriftReport(
        changed={"db.host": ("old-host", "new-host")},
        added={"feature.flag": True},
        removed={"legacy.key": "gone"},
    )


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def test_export_json_no_drift_has_drift_false():
    result = export_report(_clean_report(), ExportOptions(fmt="json"))
    data = json.loads(result)
    assert data["has_drift"] is False


def test_export_json_drift_report_structure():
    result = export_report(_drift_report(), ExportOptions(fmt="json"))
    data = json.loads(result)
    assert data["has_drift"] is True
    assert data["changed"]["db.host"] == {"old": "old-host", "new": "new-host"}
    assert data["added"]["feature.flag"] is True
    assert data["removed"]["legacy.key"] == "gone"


def test_export_json_respects_indent():
    result = export_report(_drift_report(), ExportOptions(fmt="json", indent=4))
    # 4-space indent means lines start with four spaces
    assert "    " in result


def test_export_json_no_drift_empty_sections():
    result = export_report(_clean_report(), ExportOptions(fmt="json"))
    data = json.loads(result)
    assert data["changed"] == {}
    assert data["added"] == {}
    assert data["removed"] == {}


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def test_export_csv_no_drift_returns_header_only():
    result = export_report(_clean_report(), ExportOptions(fmt="csv"))
    lines = result.strip().splitlines()
    assert lines == ["key,status,old,new"]


def test_export_csv_contains_changed_row():
    result = export_report(_drift_report(), ExportOptions(fmt="csv"))
    assert "db.host" in result
    assert "changed" in result
    assert "old-host" in result
    assert "new-host" in result


def test_export_csv_contains_added_and_removed_rows():
    result = export_report(_drift_report(), ExportOptions(fmt="csv"))
    assert "added" in result
    assert "removed" in result


def test_export_csv_header_present():
    result = export_report(_drift_report(), ExportOptions(fmt="csv"))
    assert result.startswith("key,status,old,new")


# ---------------------------------------------------------------------------
# Unknown format
# ---------------------------------------------------------------------------

def test_export_unknown_format_raises():
    with pytest.raises(ExportError, match="Unknown export format"):
        export_report(_clean_report(), ExportOptions(fmt="xml"))  # type: ignore[arg-type]

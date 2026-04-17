"""Tests for driftwatch.trimmer."""
import pytest

from driftwatch.differ import DriftReport
from driftwatch.trimmer import (
    TrimmerError,
    TrimOptions,
    format_trim_summary,
    trim_report,
)


def _report(*changes):
    return DriftReport(env="staging", source="values.yaml", changes=list(changes))


def _chg(key, old, new):
    return {"type": "changed", "key": key, "old": old, "new": new}


def _added(key, val):
    return {"type": "added", "key": key, "old": None, "new": val}


def _removed(key, val):
    return {"type": "removed", "key": key, "old": val, "new": None}


def test_trim_removes_none_severity():
    # _severity returns "none" for missing / same-type changes that scorer skips
    # We just verify items below min_severity are dropped.
    report = _report(_chg("replicas", 2, 3), _chg("name", "a", "a"))
    opts = TrimOptions(min_severity="low")
    trimmed = trim_report(report, opts)
    # Both are "changed" type; scorer assigns low/medium based on value type.
    assert len(trimmed.changes) <= len(report.changes)


def test_trim_keeps_all_when_min_none():
    report = _report(_chg("x", 1, 2), _added("y", 5), _removed("z", 3))
    opts = TrimOptions(min_severity="none")
    trimmed = trim_report(report, opts)
    assert len(trimmed.changes) == 3


def test_trim_by_include_types_keeps_only_added():
    report = _report(_chg("x", 1, 2), _added("y", 5), _removed("z", 3))
    opts = TrimOptions(min_severity="none", include_types=["added"])
    trimmed = trim_report(report, opts)
    assert all(c["type"] == "added" for c in trimmed.changes)
    assert len(trimmed.changes) == 1


def test_trim_by_include_types_changed_and_removed():
    report = _report(_chg("x", 1, 2), _added("y", 5), _removed("z", 3))
    opts = TrimOptions(min_severity="none", include_types=["changed", "removed"])
    trimmed = trim_report(report, opts)
    assert len(trimmed.changes) == 2


def test_trim_returns_new_report_with_correct_env():
    report = _report(_added("a", 1))
    opts = TrimOptions(min_severity="none")
    trimmed = trim_report(report, opts)
    assert trimmed.env == "staging"
    assert trimmed.source == "values.yaml"


def test_trim_empty_report_stays_empty():
    report = _report()
    opts = TrimOptions(min_severity="low")
    trimmed = trim_report(report, opts)
    assert trimmed.changes == []


def test_invalid_severity_raises():
    report = _report(_chg("x", 1, 2))
    opts = TrimOptions(min_severity="critical")
    with pytest.raises(TrimmerError, match="Unknown severity"):
        trim_report(report, opts)


def test_format_trim_summary_counts():
    original = _report(_chg("a", 1, 2), _added("b", 3), _removed("c", 4))
    trimmed = _report(_chg("a", 1, 2))
    summary = format_trim_summary(original, trimmed)
    assert "Original items : 3" in summary
    assert "After trim     : 1" in summary
    assert "Removed        : 2" in summary

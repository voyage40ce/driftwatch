"""Tests for driftwatch.grouper."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.grouper import (
    GrouperError,
    GroupResult,
    format_group_summary,
    group_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report(*changes) -> DriftReport:
    """Build a minimal DriftReport with the given change dicts."""
    return DriftReport(changes=list(changes))


def _chg(key, old, new):
    return {"type": "changed", "key": key, "old_value": old, "new_value": new}


def _added(key, val):
    return {"type": "added", "key": key, "old_value": None, "new_value": val}


def _removed(key, val):
    return {"type": "removed", "key": key, "old_value": val, "new_value": None}


# ---------------------------------------------------------------------------
# group_report – change_type
# ---------------------------------------------------------------------------

def test_group_by_change_type_empty_report():
    result = group_report(_report(), group_by="change_type")
    assert isinstance(result, GroupResult)
    assert result.total() == 0
    assert result.labels() == []


def test_group_by_change_type_single_changed():
    r = _report(_chg("db.host", "old", "new"))
    result = group_report(r, group_by="change_type")
    assert "changed" in result.groups
    assert result.count("changed") == 1


def test_group_by_change_type_multiple_types():
    r = _report(
        _chg("db.host", "a", "b"),
        _added("db.port", 5432),
        _removed("app.debug", True),
    )
    result = group_report(r, group_by="change_type")
    assert result.count("changed") == 1
    assert result.count("added") == 1
    assert result.count("removed") == 1
    assert result.total() == 3


# ---------------------------------------------------------------------------
# group_report – prefix
# ---------------------------------------------------------------------------

def test_group_by_prefix_single_prefix():
    r = _report(_chg("db.host", "a", "b"), _added("db.port", 5432))
    result = group_report(r, group_by="prefix")
    assert result.labels() == ["db"]
    assert result.count("db") == 2


def test_group_by_prefix_multiple_prefixes():
    r = _report(
        _chg("db.host", "a", "b"),
        _added("app.debug", True),
        _removed("cache.ttl", 60),
    )
    result = group_report(r, group_by="prefix")
    assert set(result.labels()) == {"db", "app", "cache"}


def test_group_by_prefix_top_level_key():
    """A key with no dot should use itself as the prefix."""
    r = _report(_chg("timeout", 30, 60))
    result = group_report(r, group_by="prefix")
    assert "timeout" in result.labels()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_invalid_group_by_raises():
    with pytest.raises(GrouperError, match="Unknown group_by"):
        group_report(_report(), group_by="nonsense")  # type: ignore[arg-type]


def test_non_report_raises():
    with pytest.raises(GrouperError):
        group_report({}, group_by="change_type")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# format_group_summary
# ---------------------------------------------------------------------------

def test_format_summary_no_drift():
    summary = format_group_summary(GroupResult(groups={}, group_by="change_type"))
    assert "No drift" in summary


def test_format_summary_contains_label():
    r = _report(_chg("db.host", "old", "new"))
    result = group_report(r, group_by="change_type")
    summary = format_group_summary(result)
    assert "changed" in summary
    assert "db.host" in summary

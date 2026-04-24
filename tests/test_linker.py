"""Tests for driftwatch.linker."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.linker import (
    LinkerError,
    LinkResult,
    LinkedKey,
    format_link_summary,
    link_reports,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report(*changes) -> DriftReport:
    """Build a DriftReport from (key, change_type, old, new) tuples."""
    items = [
        {"key": k, "change_type": ct, "old_value": o, "new_value": n}
        for k, ct, o, n in changes
    ]
    return DriftReport(changes=items)


# ---------------------------------------------------------------------------
# link_reports
# ---------------------------------------------------------------------------

def test_link_reports_returns_link_result():
    left = _report(("a", "changed", 1, 2))
    right = _report(("a", "changed", 1, 2))
    result = link_reports(left, right)
    assert isinstance(result, LinkResult)


def test_shared_key_agrees_when_same_change_type():
    left = _report(("db.host", "changed", "old", "new"))
    right = _report(("db.host", "changed", "old", "new2"))
    result = link_reports(left, right, left_env="staging", right_env="prod")
    assert len(result.linked) == 1
    assert result.linked[0].agrees is True


def test_shared_key_conflicts_when_different_change_type():
    left = _report(("db.host", "changed", "old", "new"))
    right = _report(("db.host", "removed", "old", None))
    result = link_reports(left, right)
    assert len(result.linked) == 1
    lk = result.linked[0]
    assert lk.agrees is False
    assert lk.left_change_type == "changed"
    assert lk.right_change_type == "removed"


def test_left_only_keys_are_captured():
    left = _report(("only.left", "added", None, "v"), ("shared", "changed", 1, 2))
    right = _report(("shared", "changed", 1, 2))
    result = link_reports(left, right)
    assert "only.left" in result.left_only
    assert "only.left" not in [lk.key for lk in result.linked]


def test_right_only_keys_are_captured():
    left = _report(("shared", "changed", 1, 2))
    right = _report(("only.right", "removed", "v", None), ("shared", "changed", 1, 2))
    result = link_reports(left, right)
    assert "only.right" in result.right_only


def test_no_shared_keys_gives_empty_linked():
    left = _report(("a", "added", None, 1))
    right = _report(("b", "added", None, 2))
    result = link_reports(left, right)
    assert result.linked == []
    assert result.left_only == ["a"]
    assert result.right_only == ["b"]


def test_has_conflicts_false_when_all_agree():
    left = _report(("x", "changed", 1, 2))
    right = _report(("x", "changed", 1, 3))
    result = link_reports(left, right)
    assert result.has_conflicts is False


def test_has_conflicts_true_when_any_disagree():
    left = _report(("x", "changed", 1, 2), ("y", "added", None, 5))
    right = _report(("x", "removed", 1, None), ("y", "added", None, 5))
    result = link_reports(left, right)
    assert result.has_conflicts is True


def test_invalid_input_raises_linker_error():
    with pytest.raises(LinkerError):
        link_reports({}, _report(("a", "added", None, 1)))  # type: ignore[arg-type]


def test_env_names_stored_in_result():
    left = _report()
    right = _report()
    result = link_reports(left, right, left_env="dev", right_env="prod")
    assert result.left_env == "dev"
    assert result.right_env == "prod"


# ---------------------------------------------------------------------------
# format_link_summary
# ---------------------------------------------------------------------------

def test_format_summary_contains_env_names():
    left = _report()
    right = _report()
    result = link_reports(left, right, left_env="alpha", right_env="beta")
    summary = format_link_summary(result)
    assert "alpha" in summary
    assert "beta" in summary


def test_format_summary_shows_conflict_count():
    left = _report(("k", "changed", 1, 2))
    right = _report(("k", "removed", 1, None))
    result = link_reports(left, right)
    summary = format_link_summary(result)
    assert "CONFLICT" in summary

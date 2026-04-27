"""Tests for driftwatch.truncator."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.truncator import (
    TruncatorError,
    TruncateResult,
    truncate_report,
    format_truncate_summary,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _change(key: str, change_type: str = "changed"):
    return {"key": key, "change_type": change_type, "expected": "a", "actual": "b"}


def _report(n: int, env: str = "prod") -> DriftReport:
    changes = [_change(f"key.{i}") for i in range(n)]
    return DriftReport(env=env, changes=changes)


# ---------------------------------------------------------------------------
# truncate_report
# ---------------------------------------------------------------------------

def test_truncate_report_requires_drift_report():
    with pytest.raises(TruncatorError, match="DriftReport"):
        truncate_report({"env": "prod", "changes": []}, limit=5)


def test_truncate_limit_less_than_one_raises():
    report = _report(3)
    with pytest.raises(TruncatorError, match="limit must be"):
        truncate_report(report, limit=0)


def test_truncate_returns_truncate_result():
    result = truncate_report(_report(5), limit=3)
    assert isinstance(result, TruncateResult)


def test_truncate_env_preserved():
    result = truncate_report(_report(2, env="staging"), limit=10)
    assert result.env == "staging"


def test_truncate_keeps_all_when_under_limit():
    result = truncate_report(_report(3), limit=10)
    assert len(result.items) == 3
    assert result.truncated is False


def test_truncate_keeps_all_when_exactly_at_limit():
    result = truncate_report(_report(5), limit=5)
    assert len(result.items) == 5
    assert result.truncated is False


def test_truncate_removes_excess_items():
    result = truncate_report(_report(10), limit=4)
    assert len(result.items) == 4
    assert result.truncated is True


def test_truncate_total_before_records_original_count():
    result = truncate_report(_report(7), limit=3)
    assert result.total_before == 7


def test_truncate_removed_count_correct():
    result = truncate_report(_report(7), limit=3)
    assert result.removed_count == 4


def test_truncate_empty_report_not_truncated():
    result = truncate_report(_report(0), limit=5)
    assert result.truncated is False
    assert result.removed_count == 0


# ---------------------------------------------------------------------------
# format_truncate_summary
# ---------------------------------------------------------------------------

def test_format_summary_not_truncated():
    result = truncate_report(_report(3), limit=10)
    summary = format_truncate_summary(result)
    assert "nothing truncated" in summary
    assert "3" in summary


def test_format_summary_truncated_shows_counts():
    result = truncate_report(_report(10), limit=4)
    summary = format_truncate_summary(result)
    assert "4" in summary
    assert "10" in summary
    assert "truncated" in summary


def test_format_summary_includes_env():
    result = truncate_report(_report(2, env="dev"), limit=5)
    summary = format_truncate_summary(result)
    assert "dev" in summary

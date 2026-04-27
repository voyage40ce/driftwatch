"""Tests for driftwatch/composer.py."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.composer import (
    ComposerError,
    ComposeResult,
    compose_reports,
    format_compose_summary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report(env: str = "prod", changes=None) -> DriftReport:
    return DriftReport(env=env, changes=changes or [])


def _change(key: str, change_type: str = "changed") -> dict:
    return {"key": key, "change_type": change_type, "expected": "a", "actual": "b"}


# ---------------------------------------------------------------------------
# compose_reports
# ---------------------------------------------------------------------------

def test_empty_list_raises():
    with pytest.raises(ComposerError, match="at least one"):
        compose_reports([])


def test_non_report_item_raises():
    with pytest.raises(ComposerError, match="not a DriftReport"):
        compose_reports([{"key": "value"}])  # type: ignore[arg-type]


def test_single_clean_report_no_drift():
    result = compose_reports([_report()])
    assert not result.has_drift
    assert result.changes == []


def test_single_drift_report_preserves_changes():
    r = _report(changes=[_change("db.host")])
    result = compose_reports([r])
    assert result.has_drift
    assert len(result.changes) == 1
    assert result.changes[0]["key"] == "db.host"


def test_env_defaults_to_first_report():
    r1 = _report(env="staging")
    r2 = _report(env="prod")
    result = compose_reports([r1, r2])
    assert result.env == "staging"


def test_env_override():
    r = _report(env="staging")
    result = compose_reports([r], env="combined")
    assert result.env == "combined"


def test_report_count_matches_input():
    reports = [_report(), _report(), _report()]
    result = compose_reports(reports)
    assert result.report_count == 3


def test_deduplication_removes_identical_key_and_type():
    change = _change("app.port")
    r1 = _report(changes=[change])
    r2 = _report(changes=[change])
    result = compose_reports([r1, r2], deduplicate=True)
    assert len(result.changes) == 1


def test_deduplication_disabled_keeps_all():
    change = _change("app.port")
    r1 = _report(changes=[change])
    r2 = _report(changes=[change])
    result = compose_reports([r1, r2], deduplicate=False)
    assert len(result.changes) == 2


def test_different_keys_not_deduplicated():
    r1 = _report(changes=[_change("a.b")])
    r2 = _report(changes=[_change("c.d")])
    result = compose_reports([r1, r2])
    assert len(result.changes) == 2


# ---------------------------------------------------------------------------
# format_compose_summary
# ---------------------------------------------------------------------------

def test_format_summary_contains_env():
    r = _report(env="prod", changes=[_change("x")])
    result = compose_reports([r])
    summary = format_compose_summary(result)
    assert "prod" in summary


def test_format_summary_shows_drift_true():
    r = _report(changes=[_change("x")])
    result = compose_reports([r])
    summary = format_compose_summary(result)
    assert "True" in summary


def test_format_summary_shows_drift_false():
    result = compose_reports([_report()])
    summary = format_compose_summary(result)
    assert "False" in summary

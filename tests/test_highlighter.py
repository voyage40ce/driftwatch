"""Tests for driftwatch.highlighter."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.highlighter import (
    HighlightOptions,
    HighlighterError,
    format_highlight_summary,
    highlight_report,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _change(key: str, change_type: str = "changed") -> dict:
    return {"key": key, "change_type": change_type, "old": "a", "new": "b"}


def _report(*keys: str) -> DriftReport:
    changes = [_change(k) for k in keys]
    return DriftReport(env="prod", changes=changes)


# ---------------------------------------------------------------------------
# highlight_report
# ---------------------------------------------------------------------------

def test_highlight_report_requires_drift_report():
    with pytest.raises(HighlighterError):
        highlight_report({})  # type: ignore


def test_no_patterns_returns_empty_highlighted():
    report = _report("db.host", "db.password", "app.debug")
    result = highlight_report(report, HighlightOptions(patterns=[]))
    assert result.highlight_count == 0
    assert not result.has_highlights
    assert len(result.all_items) == 3


def test_pattern_matches_exact_key():
    report = _report("db.host", "db.password")
    result = highlight_report(report, HighlightOptions(patterns=["db.password"]))
    assert result.highlight_count == 1
    assert result.highlighted[0]["key"] == "db.password"


def test_pattern_matches_partial_key():
    report = _report("db.host", "db.password", "app.secret")
    result = highlight_report(report, HighlightOptions(patterns=["password|secret"]))
    assert result.highlight_count == 2


def test_case_insensitive_by_default():
    report = _report("DB.PASSWORD", "app.debug")
    result = highlight_report(report, HighlightOptions(patterns=["password"]))
    assert result.highlight_count == 1


def test_case_sensitive_does_not_match_wrong_case():
    report = _report("DB.PASSWORD", "app.debug")
    result = highlight_report(
        report, HighlightOptions(patterns=["password"], case_sensitive=True)
    )
    assert result.highlight_count == 0


def test_invalid_pattern_raises():
    report = _report("key.one")
    with pytest.raises(HighlighterError, match="Invalid pattern"):
        highlight_report(report, HighlightOptions(patterns=["[invalid"]))


def test_env_is_propagated():
    report = _report("x.y")
    result = highlight_report(report)
    assert result.env == "prod"


def test_multiple_patterns_union():
    report = _report("alpha", "beta", "gamma")
    result = highlight_report(
        report, HighlightOptions(patterns=["^alpha$", "^gamma$"])
    )
    keys = [item["key"] for item in result.highlighted]
    assert sorted(keys) == ["alpha", "gamma"]


# ---------------------------------------------------------------------------
# format_highlight_summary
# ---------------------------------------------------------------------------

def test_format_summary_shows_env():
    report = _report("x")
    result = highlight_report(report, HighlightOptions(patterns=["x"]))
    summary = format_highlight_summary(result)
    assert "prod" in summary


def test_format_summary_shows_counts():
    report = _report("db.host", "db.pass")
    result = highlight_report(report, HighlightOptions(patterns=["pass"]))
    summary = format_highlight_summary(result)
    assert "2" in summary  # total
    assert "1" in summary  # highlighted


def test_format_summary_lists_highlighted_keys():
    report = _report("secret.key")
    result = highlight_report(report, HighlightOptions(patterns=["secret"]))
    summary = format_highlight_summary(result)
    assert "secret.key" in summary

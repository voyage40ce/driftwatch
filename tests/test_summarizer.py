"""Tests for driftwatch.summarizer."""
import pytest
from driftwatch.differ import DriftReport
from driftwatch.summarizer import summarize, format_summary, DriftSummary


def _clean_report() -> DriftReport:
    return DriftReport(changes={}, source={"a": 1, "b": 2})


def _drift_report() -> DriftReport:
    return DriftReport(
        changes={
            "db.host": {"type": "changed", "expected": "localhost", "actual": "prod-db"},
            "db.port": {"type": "added", "expected": None, "actual": 5432},
            "cache.ttl": {"type": "removed", "expected": 300, "actual": None},
        },
        source={"db": {"host": "localhost"}, "cache": {"ttl": 300}},
    )


def test_summarize_no_drift_has_drift_false():
    s = summarize(_clean_report(), env="staging")
    assert not s.has_drift


def test_summarize_no_drift_counts_zero():
    s = summarize(_clean_report(), env="staging")
    assert s.changed == 0
    assert s.added == 0
    assert s.removed == 0


def test_summarize_drift_report_counts():
    s = summarize(_drift_report(), env="prod")
    assert s.changed == 1
    assert s.added == 1
    assert s.removed == 1


def test_summarize_has_drift_true():
    s = summarize(_drift_report(), env="prod")
    assert s.has_drift


def test_summarize_drift_score_nonzero():
    s = summarize(_drift_report(), env="prod")
    assert s.drift_score > 0.0


def test_summarize_env_set_correctly():
    s = summarize(_clean_report(), env="dev")
    assert s.env == "dev"


def test_summarize_top_changed_respects_top_n():
    s = summarize(_drift_report(), env="prod", top_n=2)
    assert len(s.top_changed) <= 2


def test_format_summary_contains_env():
    s = summarize(_drift_report(), env="prod")
    out = format_summary(s)
    assert "prod" in out


def test_format_summary_contains_drift_score():
    s = summarize(_drift_report(), env="prod")
    out = format_summary(s)
    assert "Drift score" in out


def test_format_summary_lists_top_drifted():
    s = summarize(_drift_report(), env="prod")
    out = format_summary(s)
    assert "Top drifted" in out

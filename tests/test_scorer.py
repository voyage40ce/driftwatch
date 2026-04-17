"""Tests for driftwatch.scorer."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport, Change
from driftwatch.scorer import DriftScore, _severity, format_score, score_report


def _report(*changes: Change, env: str = "test") -> DriftReport:
    return DriftReport(env=env, changes=list(changes))


def _chg(key: str, t: str) -> Change:
    return Change(key=key, change_type=t, source_value="a", deployed_value="b")


# --- _severity ---

def test_severity_none():
    assert _severity(0) == "none"


def test_severity_low():
    assert _severity(1.0) == "low"


def test_severity_medium():
    assert _severity(3.0) == "medium"


def test_severity_high():
    assert _severity(6.0) == "high"


# --- score_report ---

def test_score_no_changes():
    ds = score_report(_report())
    assert ds.total == 0.0
    assert ds.severity == "none"


def test_score_counts_changed():
    ds = score_report(_report(_chg("a", "changed"), _chg("b", "changed")))
    assert ds.changed == 2
    assert ds.total == 2.0


def test_score_counts_added():
    ds = score_report(_report(_chg("x", "added")))
    assert ds.added == 1
    assert ds.total == 0.5


def test_score_counts_removed():
    ds = score_report(_report(_chg("x", "removed")))
    assert ds.removed == 1
    assert ds.total == 0.8


def test_score_mixed():
    ds = score_report(_report(_chg("a", "changed"), _chg("b", "added"), _chg("c", "removed")))
    assert ds.total == round(1.0 + 0.5 + 0.8, 2)
    assert ds.severity == "medium"


def test_score_env_preserved():
    ds = score_report(_report(env="prod"))
    assert ds.env == "prod"


# --- format_score ---

def test_format_score_contains_severity():
    ds = DriftScore(env="staging", total=3.0, changed=2, added=1, removed=0, severity="medium")
    out = format_score(ds)
    assert "MEDIUM" in out
    assert "staging" in out
    assert "3.0" in out

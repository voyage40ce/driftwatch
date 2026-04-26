"""Tests for driftwatch/classifier.py"""
from __future__ import annotations

import pytest

from driftwatch.classifier import (
    ClassifierError,
    ClassifiedItem,
    ClassifyResult,
    classify,
    format_classify_summary,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)
from driftwatch.differ import DriftReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Any


@dataclass
class _Change:
    key: str
    change_type: str
    old_value: Any = None
    new_value: Any = None


def _report(changes=None, env="test"):
    r = DriftReport(env=env)
    r.changes = changes or []
    return r


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------

def test_classify_requires_drift_report():
    with pytest.raises(ClassifierError):
        classify({"key": "value"})  # type: ignore


def test_classify_empty_report_returns_empty_result():
    result = classify(_report())
    assert isinstance(result, ClassifyResult)
    assert result.items == []


def test_classify_changed_value_is_low_severity_value_category():
    changes = [_Change("app.port", "changed", old_value="8080", new_value="9090")]
    result = classify(_report(changes))
    assert len(result.items) == 1
    item = result.items[0]
    assert item.severity == SEVERITY_LOW
    assert item.category == "value"
    assert item.change_type == "changed"


def test_classify_added_key_is_structural_medium():
    changes = [_Change("feature.flag", "added", new_value=True)]
    result = classify(_report(changes))
    item = result.items[0]
    assert item.category == "structural"
    assert item.severity == SEVERITY_MEDIUM


def test_classify_removed_key_is_structural_medium():
    changes = [_Change("db.host", "removed", old_value="localhost")]
    result = classify(_report(changes))
    item = result.items[0]
    assert item.category == "structural"
    assert item.severity == SEVERITY_MEDIUM


def test_classify_password_key_is_high_security():
    changes = [_Change("db.password", "changed", old_value="old", new_value="new")]
    result = classify(_report(changes))
    item = result.items[0]
    assert item.severity == SEVERITY_HIGH
    assert item.category == "security"


def test_classify_token_key_is_high_security():
    changes = [_Change("auth.token", "added", new_value="abc123")]
    result = classify(_report(changes))
    assert result.items[0].severity == SEVERITY_HIGH


def test_classify_has_high_true_when_high_present():
    changes = [_Change("api.secret", "changed", old_value="x", new_value="y")]
    result = classify(_report(changes))
    assert result.has_high is True


def test_classify_has_high_false_when_no_high():
    changes = [_Change("app.port", "changed", old_value="80", new_value="443")]
    result = classify(_report(changes))
    assert result.has_high is False


def test_by_severity_filters_correctly():
    changes = [
        _Change("db.password", "changed", old_value="a", new_value="b"),
        _Change("app.port", "changed", old_value="80", new_value="81"),
    ]
    result = classify(_report(changes))
    high = result.by_severity(SEVERITY_HIGH)
    low = result.by_severity(SEVERITY_LOW)
    assert len(high) == 1
    assert len(low) == 1


def test_by_category_filters_correctly():
    changes = [
        _Change("new.key", "added", new_value="v"),
        _Change("app.name", "changed", old_value="a", new_value="b"),
    ]
    result = classify(_report(changes))
    structural = result.by_category("structural")
    value = result.by_category("value")
    assert len(structural) == 1
    assert len(value) == 1


# ---------------------------------------------------------------------------
# format_classify_summary()
# ---------------------------------------------------------------------------

def test_format_summary_no_items_shows_no_drift():
    result = ClassifyResult(env="staging")
    summary = format_classify_summary(result)
    assert "No drift" in summary
    assert "staging" in summary


def test_format_summary_shows_high_severity():
    result = ClassifyResult(env="prod")
    result.items = [
        ClassifiedItem("db.password", "changed", SEVERITY_HIGH, "security")
    ]
    summary = format_classify_summary(result)
    assert "HIGH" in summary
    assert "db.password" in summary

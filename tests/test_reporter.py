"""Tests for driftwatch.reporter formatting logic."""

import pytest
from driftwatch.differ import DriftReport
from driftwatch.reporter import format_report, ReportOptions


NO_COLOR = ReportOptions(use_color=False)


def make_report(diffs: dict) -> DriftReport:
    has = bool(diffs)
    return DriftReport(diffs=diffs, has_drift=has)


def test_format_report_no_drift():
    report = make_report({})
    output = format_report(report, NO_COLOR)
    assert "No drift detected" in output
    assert "OK" in output


def test_format_report_shows_drift_status():
    report = make_report(
        {"app.port": {"type": "changed", "expected": 8080, "actual": 9090}}
    )
    output = format_report(report, NO_COLOR)
    assert "DRIFT" in output
    assert "1 difference" in output


def test_format_report_changed_key():
    report = make_report(
        {"db.host": {"type": "changed", "expected": "localhost", "actual": "prod-db"}}
    )
    output = format_report(report, NO_COLOR)
    assert "CHANGED" in output
    assert "db.host" in output
    assert "localhost" in output
    assert "prod-db" in output


def test_format_report_added_key():
    report = make_report(
        {"feature.flag": {"type": "added", "actual": True}}
    )
    output = format_report(report, NO_COLOR)
    assert "ADDED" in output
    assert "feature.flag" in output


def test_format_report_removed_key():
    report = make_report(
        {"legacy.option": {"type": "removed", "expected": "old_value"}}
    )
    output = format_report(report, NO_COLOR)
    assert "REMOVED" in output
    assert "legacy.option" in output


def test_format_report_multiple_diffs_sorted():
    report = make_report({
        "z.key": {"type": "added", "actual": 1},
        "a.key": {"type": "removed", "expected": 2},
    })
    output = format_report(report, NO_COLOR)
    a_pos = output.index("a.key")
    z_pos = output.index("z.key")
    assert a_pos < z_pos


def test_format_report_color_enabled():
    report = make_report(
        {"app.debug": {"type": "changed", "expected": False, "actual": True}}
    )
    colored = format_report(report, ReportOptions(use_color=True))
    assert "\033[" in colored


def test_format_report_color_disabled():
    report = make_report(
        {"app.debug": {"type": "changed", "expected": False, "actual": True}}
    )
    plain = format_report(report, NO_COLOR)
    assert "\033[" not in plain

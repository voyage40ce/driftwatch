"""Unit tests for driftwatch.differ."""

import pytest

from driftwatch.differ import DriftReport, diff


def test_no_drift_identical_configs():
    cfg = {"app": "web", "database": {"host": "localhost", "port": 5432}}
    report = diff(cfg, cfg)
    assert not report.has_drift


def test_detects_changed_value():
    expected = {"database": {"host": "localhost"}}
    actual = {"database": {"host": "prod-db.example.com"}}
    report = diff(expected, actual)
    assert "database.host" in report.changed
    assert report.changed["database.host"] == ("localhost", "prod-db.example.com")
    assert not report.added
    assert not report.removed


def test_detects_added_key():
    expected = {"app": "web"}
    actual = {"app": "web", "debug": True}
    report = diff(expected, actual)
    assert "debug" in report.added
    assert report.added["debug"] is True


def test_detects_removed_key():
    expected = {"app": "web", "replicas": 3}
    actual = {"app": "web"}
    report = diff(expected, actual)
    assert "replicas" in report.removed
    assert report.removed["replicas"] == 3


def test_nested_keys_use_dot_notation():
    expected = {"service": {"timeouts": {"read": 30}}}
    actual = {"service": {"timeouts": {"read": 60}}}
    report = diff(expected, actual)
    assert "service.timeouts.read" in report.changed


def test_has_drift_false_when_clean():
    report = DriftReport()
    assert not report.has_drift


def test_has_drift_true_when_changed():
    report = DriftReport(changed={"key": ("a", "b")})
    assert report.has_drift


def test_empty_configs_no_drift():
    assert not diff({}, {}).has_drift

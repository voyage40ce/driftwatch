"""Tests for driftwatch.watcher."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from driftwatch.watcher import WatchOptions, WatchError, watch, _load_and_diff
from driftwatch.differ import DriftReport
from driftwatch.loader import ConfigLoadError


# ---------------------------------------------------------------------------
# _load_and_diff
# ---------------------------------------------------------------------------

def test_load_and_diff_raises_watch_error_on_config_load_error():
    with patch("driftwatch.watcher.load_pair", side_effect=ConfigLoadError("bad")):
        with pytest.raises(WatchError, match="bad"):
            _load_and_diff("a.yaml", "b.yaml")


def test_load_and_diff_returns_report():
    cfg = {"key": "value"}
    with patch("driftwatch.watcher.load_pair", return_value=(cfg, cfg)):
        report = _load_and_diff("a.yaml", "b.yaml")
    assert isinstance(report, DriftReport)
    assert report.changes == []


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

def _make_opts(on_drift=None, on_clear=None, max_iterations=1):
    opts = WatchOptions(
        source="src.yaml",
        deployed="dep.yaml",
        interval=0.0,
        max_iterations=max_iterations,
    )
    if on_drift:
        opts.on_drift = on_drift
    if on_clear:
        opts.on_clear = on_clear
    return opts


def test_watch_calls_on_drift_when_drift_detected():
    drift_report = DriftReport(changes=[MagicMock()])
    on_drift = MagicMock()

    with patch("driftwatch.watcher._load_and_diff", return_value=drift_report):
        with patch("driftwatch.watcher.time.sleep"):
            watch(_make_opts(on_drift=on_drift, max_iterations=1))

    on_drift.assert_called_once_with(drift_report)


def test_watch_calls_on_clear_when_drift_resolves():
    clean_report = DriftReport(changes=[])
    drift_report = DriftReport(changes=[MagicMock()])
    on_clear = MagicMock()
    reports = iter([drift_report, clean_report])

    with patch("driftwatch.watcher._load_and_diff", side_effect=reports):
        with patch("driftwatch.watcher.time.sleep"):
            watch(_make_opts(on_clear=on_clear, max_iterations=2))

    on_clear.assert_called_once()


def test_watch_continues_on_watch_error():
    clean_report = DriftReport(changes=[])
    side_effects = [WatchError("oops"), clean_report]
    on_drift = MagicMock()

    with patch("driftwatch.watcher._load_and_diff", side_effect=side_effects):
        with patch("driftwatch.watcher.time.sleep"):
            watch(_make_opts(on_drift=on_drift, max_iterations=2))

    on_drift.assert_not_called()


def test_watch_no_clear_callback_without_prior_drift():
    clean_report = DriftReport(changes=[])
    on_clear = MagicMock()

    with patch("driftwatch.watcher._load_and_diff", return_value=clean_report):
        with patch("driftwatch.watcher.time.sleep"):
            watch(_make_opts(on_clear=on_clear, max_iterations=2))

    on_clear.assert_not_called()

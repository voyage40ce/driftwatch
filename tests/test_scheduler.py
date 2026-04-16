"""Tests for driftwatch.scheduler."""
import threading
import pytest
from unittest.mock import patch, MagicMock

from driftwatch.scheduler import ScheduleOptions, run_scheduler, SchedulerError
from driftwatch.differ import DriftReport
from driftwatch.watcher import WatchError


def _make_opts(**kwargs) -> ScheduleOptions:
    defaults = dict(source="s.yaml", deployed="d.yaml", env="test", interval=0.01, max_runs=1)
    defaults.update(kwargs)
    return ScheduleOptions(**defaults)


def _clean_report():
    return DriftReport(changed={}, added={}, removed={})


def _drift_report():
    return DriftReport(changed={"key": ("a", "b")}, added={}, removed={})


def test_run_scheduler_calls_on_drift_when_drift():
    report = _drift_report()
    on_drift = MagicMock()
    opts = _make_opts(on_drift=on_drift, max_runs=1)
    with patch("driftwatch.scheduler._run_once", return_value=report):
        run_scheduler(opts)
    on_drift.assert_called_once_with(report)


def test_run_scheduler_no_drift_no_on_drift_call():
    report = _clean_report()
    on_drift = MagicMock()
    opts = _make_opts(on_drift=on_drift, max_runs=1)
    with patch("driftwatch.scheduler._run_once", return_value=report):
        run_scheduler(opts)
    on_drift.assert_not_called()


def test_run_scheduler_calls_on_clear_when_drift_resolves():
    reports = [_drift_report(), _clean_report()]
    on_clear = MagicMock()
    opts = _make_opts(on_clear=on_clear, max_runs=2)
    with patch("driftwatch.scheduler._run_once", side_effect=reports):
        run_scheduler(opts)
    on_clear.assert_called_once()


def test_run_scheduler_calls_on_error_on_watch_error():
    on_error = MagicMock()
    opts = _make_opts(on_error=on_error, max_runs=1)
    with patch("driftwatch.scheduler._run_once", side_effect=WatchError("boom")):
        run_scheduler(opts)
    on_error.assert_called_once()


def test_run_scheduler_respects_stop_event():
    stop = threading.Event()
    call_count = {"n": 0}

    def fake_run_once(opts):
        call_count["n"] += 1
        stop.set()
        return _clean_report()

    opts = _make_opts(max_runs=None, interval=0.01)
    with patch("driftwatch.scheduler._run_once", side_effect=fake_run_once):
        run_scheduler(opts, stop_event=stop)
    assert call_count["n"] == 1


def test_run_scheduler_max_runs_limits_iterations():
    call_count = {"n": 0}

    def fake_run_once(opts):
        call_count["n"] += 1
        return _clean_report()

    opts = _make_opts(max_runs=3, interval=0)
    with patch("driftwatch.scheduler._run_once", side_effect=fake_run_once):
        run_scheduler(opts)
    assert call_count["n"] == 3

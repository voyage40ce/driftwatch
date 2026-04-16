"""Tests for driftwatch.commands.scheduler_cmd."""
import argparse
import pytest
from unittest.mock import patch, MagicMock

from driftwatch.commands.scheduler_cmd import _dispatch, register
from driftwatch.differ import DriftReport


def _ns(**kwargs):
    defaults = dict(
        source="s.yaml",
        deployed="d.yaml",
        env="prod",
        interval=0.01,
        max_runs=1,
        no_color=True,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _clean():
    return DriftReport(changed={}, added={}, removed={})


def test_dispatch_returns_zero_on_success():
    with patch("driftwatch.commands.scheduler_cmd.run_scheduler") as mock_run:
        result = _dispatch(_ns())
    assert result == 0
    mock_run.assert_called_once()


def test_dispatch_passes_interval_to_options():
    captured = {}

    def fake_run(opts, stop_event=None):
        captured["interval"] = opts.interval

    with patch("driftwatch.commands.scheduler_cmd.run_scheduler", side_effect=fake_run):
        _dispatch(_ns(interval=42.0))

    assert captured["interval"] == 42.0


def test_dispatch_passes_max_runs_to_options():
    captured = {}

    def fake_run(opts, stop_event=None):
        captured["max_runs"] = opts.max_runs

    with patch("driftwatch.commands.scheduler_cmd.run_scheduler", side_effect=fake_run):
        _dispatch(_ns(max_runs=5))

    assert captured["max_runs"] == 5


def test_dispatch_returns_two_on_fatal_error():
    with patch("driftwatch.commands.scheduler_cmd.run_scheduler", side_effect=RuntimeError("bad")):
        result = _dispatch(_ns())
    assert result == 2


def test_register_adds_schedule_subcommand():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    register(subs)
    ns = parser.parse_args(["schedule", "s.yaml", "d.yaml"])
    assert ns.source == "s.yaml"
    assert ns.deployed == "d.yaml"

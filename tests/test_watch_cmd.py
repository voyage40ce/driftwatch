"""Tests for driftwatch.commands.watch_cmd."""

from __future__ import annotations

import argparse
import pytest
from unittest.mock import patch, MagicMock

from driftwatch.commands.watch_cmd import _dispatch, _add_watch_parser
from driftwatch.watcher import WatchError
from driftwatch.differ import DriftReport


def _ns(**kwargs):
    defaults = dict(
        source="src.yaml",
        deployed="dep.yaml",
        interval=0.0,
        no_color=True,
        iterations=1,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_dispatch_returns_zero_on_clean_run():
    with patch("driftwatch.commands.watch_cmd.watch") as mock_watch:
        result = _dispatch(_ns())
    assert result == 0
    mock_watch.assert_called_once()


def test_dispatch_returns_two_on_watch_error():
    with patch(
        "driftwatch.commands.watch_cmd.watch", side_effect=WatchError("boom")
    ):
        result = _dispatch(_ns())
    assert result == 2


def test_dispatch_passes_interval_to_options():
    captured = {}

    def fake_watch(opts):
        captured["interval"] = opts.interval

    with patch("driftwatch.commands.watch_cmd.watch", side_effect=fake_watch):
        _dispatch(_ns(interval=15.0))

    assert captured["interval"] == 15.0


def test_dispatch_on_drift_calls_print_report():
    report = DriftReport(changes=[MagicMock()])
    captured_report = {}

    def fake_watch(opts):
        opts.on_drift(report)

    with patch("driftwatch.commands.watch_cmd.watch", side_effect=fake_watch):
        with patch("driftwatch.commands.watch_cmd.print_report") as mock_print:
            _dispatch(_ns())

    mock_print.assert_called_once()


def test_dispatch_keyboard_interrupt_returns_zero():
    with patch(
        "driftwatch.commands.watch_cmd.watch", side_effect=KeyboardInterrupt
    ):
        result = _dispatch(_ns())
    assert result == 0


def test_add_watch_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    _add_watch_parser(subparsers)
    ns = parser.parse_args(["watch", "src.yaml", "dep.yaml", "--interval", "5"])
    assert ns.source == "src.yaml"
    assert ns.deployed == "dep.yaml"
    assert ns.interval == 5.0

"""Tests for driftwatch.commands.notify_cmd."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from driftwatch.commands.notify_cmd import _dispatch, _add_notify_parser
from driftwatch.notifier import NotifyError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _ns(tmp_path: Path, **kwargs) -> argparse.Namespace:
    expected = _write(tmp_path / "expected.yaml", "key: value\n")
    actual = _write(tmp_path / "actual.yaml", kwargs.pop("actual_content", "key: value\n"))
    defaults = dict(
        expected=str(expected),
        actual=str(actual),
        webhook="http://example.com/hook",
        env="test",
        only_drift=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dispatch_no_drift_exits_zero(tmp_path):
    ns = _ns(tmp_path)
    with patch("driftwatch.commands.notify_cmd.send_webhook") as mock_send:
        result = _dispatch(ns)
    assert result == 0
    mock_send.assert_called_once()


def test_dispatch_drift_exits_one(tmp_path):
    ns = _ns(tmp_path, actual_content="key: changed\n")
    with patch("driftwatch.commands.notify_cmd.send_webhook") as mock_send:
        result = _dispatch(ns)
    assert result == 1
    mock_send.assert_called_once()


def test_dispatch_missing_file_exits_two(tmp_path):
    ns = _ns(tmp_path)
    ns.expected = str(tmp_path / "nonexistent.yaml")
    result = _dispatch(ns)
    assert result == 2


def test_dispatch_notify_error_exits_three(tmp_path):
    ns = _ns(tmp_path)
    with patch(
        "driftwatch.commands.notify_cmd.send_webhook",
        side_effect=NotifyError("connection refused"),
    ):
        result = _dispatch(ns)
    assert result == 3


def test_dispatch_only_drift_skips_when_clean(tmp_path):
    ns = _ns(tmp_path, only_drift=True)
    sender = MagicMock()
    with patch("driftwatch.commands.notify_cmd.notify_if_drift", wraps=lambda r, o, **kw: False) as mock_ni:
        result = _dispatch(ns)
    assert result == 0


def test_dispatch_only_drift_sends_when_drifted(tmp_path):
    ns = _ns(tmp_path, actual_content="key: changed\n", only_drift=True)
    with patch("driftwatch.commands.notify_cmd.notify_if_drift", return_value=True) as mock_ni:
        result = _dispatch(ns)
    assert result == 1
    mock_ni.assert_called_once()


def test_add_notify_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _add_notify_parser(sub)
    ns = parser.parse_args(
        ["notify", "exp.yaml", "act.yaml", "--webhook", "http://x.com"]
    )
    assert ns.webhook == "http://x.com"
    assert ns.env == "unknown"
    assert ns.only_drift is False

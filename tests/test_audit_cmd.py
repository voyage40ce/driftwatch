"""Tests for driftwatch/commands/audit_cmd.py."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from driftwatch.audit import AuditError
from driftwatch.commands.audit_cmd import _cmd_list, _cmd_clear, _print_entry


def _ns(**kwargs):
    defaults = {"env": None, "limit": 20}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ── _cmd_list ────────────────────────────────────────────────────────────────

def test_cmd_list_returns_zero_when_no_entries():
    with patch("driftwatch.commands.audit_cmd.list_entries", return_value=[]):
        assert _cmd_list(_ns()) == 0


def test_cmd_list_returns_zero_with_entries():
    entries = [
        {"timestamp": "2024-01-01T00:00:00", "env": "prod", "has_drift": True, "change_count": 3},
    ]
    with patch("driftwatch.commands.audit_cmd.list_entries", return_value=entries):
        assert _cmd_list(_ns()) == 0


def test_cmd_list_passes_env_filter():
    with patch("driftwatch.commands.audit_cmd.list_entries", return_value=[]) as mock:
        _cmd_list(_ns(env="staging"))
        mock.assert_called_once_with(env="staging", limit=20)


def test_cmd_list_passes_limit():
    with patch("driftwatch.commands.audit_cmd.list_entries", return_value=[]) as mock:
        _cmd_list(_ns(limit=5))
        mock.assert_called_once_with(env=None, limit=5)


def test_cmd_list_returns_two_on_audit_error():
    with patch("driftwatch.commands.audit_cmd.list_entries", side_effect=AuditError("boom")):
        assert _cmd_list(_ns()) == 2


# ── _cmd_clear ───────────────────────────────────────────────────────────────

def test_cmd_clear_returns_zero():
    with patch("driftwatch.commands.audit_cmd.clear_entries", return_value=4):
        assert _cmd_clear(_ns()) == 0


def test_cmd_clear_prints_removed_count(capsys):
    with patch("driftwatch.commands.audit_cmd.clear_entries", return_value=7):
        _cmd_clear(_ns())
    assert "7" in capsys.readouterr().out


def test_cmd_clear_returns_two_on_audit_error():
    with patch("driftwatch.commands.audit_cmd.clear_entries", side_effect=AuditError("fail")):
        assert _cmd_clear(_ns()) == 2


# ── _print_entry ─────────────────────────────────────────────────────────────

def test_print_entry_shows_drift_status(capsys):
    entry = {"timestamp": "2024-06-01T12:00:00", "env": "prod", "has_drift": True, "change_count": 2}
    _print_entry(entry)
    out = capsys.readouterr().out
    assert "DRIFT" in out
    assert "prod" in out
    assert "2" in out


def test_print_entry_shows_ok_status(capsys):
    entry = {"timestamp": "2024-06-01T12:00:00", "env": "dev", "has_drift": False, "change_count": 0}
    _print_entry(entry)
    assert "OK" in capsys.readouterr().out

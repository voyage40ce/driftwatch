"""Tests for driftwatch.commands.archiver_cmd."""
import argparse
import pytest
from unittest.mock import patch, MagicMock
from driftwatch.commands.archiver_cmd import _dispatch
from driftwatch.differ import DriftReport
from driftwatch.archiver import ArchivedReport
import time


def _ns(**kwargs):
    base = dict(archive_cmd="save", source="s.yaml", deployed="d.yaml", env="prod", limit=20)
    base.update(kwargs)
    return argparse.Namespace(**base)


def _clean():
    return DriftReport(has_drift=False, changes=[])


def _drift():
    from dataclasses import dataclass
    @dataclass
    class C:
        key = "x"; source = 1; deployed = 2; kind = "changed"
    return DriftReport(has_drift=True, changes=[C()])


def _archived(env="prod", has_drift=False):
    return ArchivedReport(env=env, timestamp=time.time(), has_drift=has_drift, changes=[], path="/tmp/x.gz")


def test_save_no_drift_returns_zero(tmp_path):
    with patch("driftwatch.commands.archiver_cmd.load_pair", return_value=({}, {})), \
         patch("driftwatch.commands.archiver_cmd.diff", return_value=_clean()), \
         patch("driftwatch.commands.archiver_cmd.archive_report", return_value=_archived()):
        assert _dispatch(_ns(archive_cmd="save")) == 0


def test_save_drift_returns_one(tmp_path):
    with patch("driftwatch.commands.archiver_cmd.load_pair", return_value=({}, {})), \
         patch("driftwatch.commands.archiver_cmd.diff", return_value=_drift()), \
         patch("driftwatch.commands.archiver_cmd.archive_report", return_value=_archived(has_drift=True)):
        assert _dispatch(_ns(archive_cmd="save")) == 1


def test_save_missing_file_returns_two():
    from driftwatch.loader import ConfigLoadError
    with patch("driftwatch.commands.archiver_cmd.load_pair", side_effect=ConfigLoadError("missing")):
        assert _dispatch(_ns(archive_cmd="save")) == 2


def test_list_no_entries(capsys):
    with patch("driftwatch.commands.archiver_cmd.load_archives", return_value=[]):
        rc = _dispatch(_ns(archive_cmd="list", env=None))
    assert rc == 0
    assert "no archives" in capsys.readouterr().out


def test_list_shows_entries(capsys):
    entries = [_archived(env="prod", has_drift=False), _archived(env="prod", has_drift=True)]
    with patch("driftwatch.commands.archiver_cmd.load_archives", return_value=entries):
        rc = _dispatch(_ns(archive_cmd="list", env="prod"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod" in out


def test_clear_returns_zero(capsys):
    with patch("driftwatch.commands.archiver_cmd.clear_archives", return_value=3):
        rc = _dispatch(_ns(archive_cmd="clear", env=None))
    assert rc == 0
    assert "3" in capsys.readouterr().out

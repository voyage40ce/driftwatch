"""Tests for driftwatch.commands.diffstore_cmd."""
import argparse
import pytest
from pathlib import Path
from driftwatch.commands.diffstore_cmd import _dispatch
from driftwatch.diffstore import record_diff
from driftwatch.differ import DriftReport, DriftChange


def _ns(**kwargs):
    defaults = {"diffstore_cmd": "list", "env": "staging", "limit": 20, "store_dir": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _clean():
    return DriftReport(has_drift=False, changes=[])


def _drift():
    return DriftReport(
        has_drift=True,
        changes=[DriftChange(key="x", source_value="a", deployed_value="b")],
    )


def test_list_no_entries_returns_zero(tmp_path, capsys):
    ns = _ns(store_dir=str(tmp_path))
    result = _dispatch(ns)
    assert result == 0
    assert "No stored diffs" in capsys.readouterr().out


def test_list_shows_entries(tmp_path, capsys):
    record_diff(_clean(), "staging", base_dir=tmp_path)
    record_diff(_drift(), "staging", base_dir=tmp_path)
    ns = _ns(store_dir=str(tmp_path))
    result = _dispatch(ns)
    assert result == 0
    out = capsys.readouterr().out
    assert "staging" in out
    assert "DRIFT" in out
    assert "clean" in out


def test_list_respects_limit(tmp_path, capsys):
    for _ in range(5):
        record_diff(_clean(), "staging", base_dir=tmp_path)
    ns = _ns(store_dir=str(tmp_path), limit=2)
    _dispatch(ns)
    out = capsys.readouterr().out
    assert out.count("staging") == 2


def test_clear_returns_zero(tmp_path, capsys):
    record_diff(_clean(), "staging", base_dir=tmp_path)
    ns = _ns(diffstore_cmd="clear", store_dir=str(tmp_path))
    result = _dispatch(ns)
    assert result == 0
    assert "Cleared" in capsys.readouterr().out


def test_clear_missing_env_returns_zero(tmp_path, capsys):
    ns = _ns(diffstore_cmd="clear", env="ghost", store_dir=str(tmp_path))
    result = _dispatch(ns)
    assert result == 0
    assert "0" in capsys.readouterr().out

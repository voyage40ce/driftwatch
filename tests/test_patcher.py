"""Tests for driftwatch.patcher and commands.patcher_cmd."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest
import yaml

from driftwatch.differ import DriftReport
from driftwatch.patcher import PatchResult, format_patch_summary, patch_config


def _report(*changes):
    return DriftReport(changes=list(changes))


def _chg(key, expected, actual):
    return {"key": key, "type": "changed", "expected": expected, "actual": actual}


def _added(key, expected):
    return {"key": key, "type": "added", "expected": expected, "actual": None}


def _removed(key, actual):
    return {"key": key, "type": "removed", "expected": None, "actual": actual}


def test_patch_applies_changed_key():
    config = {"db": {"host": "old"}}
    report = _report(_chg("db.host", "new", "old"))
    result = patch_config(config, report)
    assert result.patched["db"]["host"] == "new"
    assert "db.host" in result.applied


def test_patch_applies_added_key():
    config = {"a": 1}
    report = _report(_added("b", 2))
    result = patch_config(config, report)
    assert result.patched["b"] == 2


def test_patch_removes_key():
    config = {"a": 1, "b": 2}
    report = _report(_removed("b", 2))
    result = patch_config(config, report)
    assert "b" not in result.patched


def test_patch_skips_listed_keys():
    config = {"a": "old"}
    report = _report(_chg("a", "new", "old"))
    result = patch_config(config, report, skip_keys=["a"])
    assert result.patched["a"] == "old"
    assert "a" in result.skipped
    assert "a" not in result.applied


def test_dry_run_does_not_mutate():
    config = {"x": 1}
    report = _report(_chg("x", 99, 1))
    result = patch_config(config, report, dry_run=True)
    assert result.patched["x"] == 1
    assert "x" in result.applied  # still recorded as would-apply


def test_original_config_not_mutated():
    config = {"a": 1}
    report = _report(_chg("a", 2, 1))
    patch_config(config, report)
    assert config["a"] == 1


def test_format_patch_summary_contains_counts():
    result = PatchResult(patched={}, applied=["a", "b"], skipped=["c"])
    summary = format_patch_summary(result)
    assert "2 applied" in summary
    assert "1 skipped" in summary


# --- CLI command tests ---

def _write(tmp_path: Path, name: str, data: dict) -> str:
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def _ns(tmp_path, source_data, deployed_data, **kwargs):
    ns = argparse.Namespace(
        source=_write(tmp_path, "source.yaml", source_data),
        deployed=_write(tmp_path, "deployed.yaml", deployed_data),
        output="-",
        skip=[],
        dry_run=False,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_cmd_no_drift_returns_zero(tmp_path, capsys):
    from driftwatch.commands.patcher_cmd import _dispatch
    ns = _ns(tmp_path, {"a": 1}, {"a": 1})
    assert _dispatch(ns) == 0


def test_cmd_drift_applies_and_returns_zero(tmp_path, capsys):
    from driftwatch.commands.patcher_cmd import _dispatch
    ns = _ns(tmp_path, {"a": 2}, {"a": 1})
    assert _dispatch(ns) == 0
    out = capsys.readouterr().out
    assert "1 applied" in out


def test_cmd_missing_file_returns_two(tmp_path):
    from driftwatch.commands.patcher_cmd import _dispatch
    ns = argparse.Namespace(
        source=str(tmp_path / "missing.yaml"),
        deployed=str(tmp_path / "also_missing.yaml"),
        output="-", skip=[], dry_run=False,
    )
    assert _dispatch(ns) == 2

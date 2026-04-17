"""Tests for driftwatch.commands.filter_cmd"""
import argparse
import pytest
from pathlib import Path
from driftwatch.commands.filter_cmd import _dispatch


def _write(tmp_path, name, data):
    import yaml
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def _ns(source, deployed, include=None, exclude=None,
        changed_only=False, added_only=False, removed_only=False, no_color=True):
    ns = argparse.Namespace(
        source=source, deployed=deployed,
        include=include or [], exclude=exclude or [],
        changed_only=changed_only, added_only=added_only,
        removed_only=removed_only, no_color=no_color,
    )
    return ns


def test_no_drift_returns_zero(tmp_path):
    cfg = {"a": 1, "b": 2}
    s = _write(tmp_path, "s.yaml", cfg)
    d = _write(tmp_path, "d.yaml", cfg)
    assert _dispatch(_ns(s, d)) == 0


def test_drift_returns_one(tmp_path):
    s = _write(tmp_path, "s.yaml", {"a": 1})
    d = _write(tmp_path, "d.yaml", {"a": 99})
    assert _dispatch(_ns(s, d)) == 1


def test_missing_file_returns_two(tmp_path):
    s = _write(tmp_path, "s.yaml", {"a": 1})
    assert _dispatch(_ns(s, str(tmp_path / "missing.yaml"))) == 2


def test_include_filters_out_all_returns_zero(tmp_path):
    s = _write(tmp_path, "s.yaml", {"a": 1, "b": 2})
    d = _write(tmp_path, "d.yaml", {"a": 99, "b": 2})
    # include only "b.*" which has no drift
    assert _dispatch(_ns(s, d, include=["b"])) == 0


def test_exclude_filters_drifted_key_returns_zero(tmp_path):
    s = _write(tmp_path, "s.yaml", {"a": 1})
    d = _write(tmp_path, "d.yaml", {"a": 99})
    assert _dispatch(_ns(s, d, exclude=["a"])) == 0

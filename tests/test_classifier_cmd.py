"""Tests for driftwatch/commands/classifier_cmd.py"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from driftwatch.commands.classifier_cmd import _dispatch, _add_classifier_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)


def _ns(tmp_path, source_content, deployed_content, env="test",
        min_severity=None, category=None):
    src = _write(tmp_path, "source.yaml", source_content)
    dep = _write(tmp_path, "deployed.yaml", deployed_content)
    ns = argparse.Namespace(
        source=src,
        deployed=dep,
        env=env,
        min_severity=min_severity,
        category=category,
    )
    return ns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_drift_returns_zero(tmp_path):
    cfg = "app:\n  port: 8080\n"
    ns = _ns(tmp_path, cfg, cfg)
    assert _dispatch(ns) == 0


def test_value_drift_returns_zero_no_high(tmp_path):
    src = "app:\n  port: 8080\n"
    dep = "app:\n  port: 9090\n"
    ns = _ns(tmp_path, src, dep)
    assert _dispatch(ns) == 0


def test_high_severity_drift_returns_one(tmp_path):
    src = "db:\n  password: old\n"
    dep = "db:\n  password: new\n"
    ns = _ns(tmp_path, src, dep)
    assert _dispatch(ns) == 1


def test_missing_source_returns_two(tmp_path):
    dep = _write(tmp_path, "deployed.yaml", "app: 1\n")
    ns = argparse.Namespace(
        source=str(tmp_path / "missing.yaml"),
        deployed=dep,
        env="test",
        min_severity=None,
        category=None,
    )
    assert _dispatch(ns) == 2


def test_min_severity_filters_output(tmp_path, capsys):
    src = "app:\n  port: 80\n"
    dep = "app:\n  port: 81\n"
    ns = _ns(tmp_path, src, dep, min_severity="high")
    _dispatch(ns)
    captured = capsys.readouterr()
    # low-severity port change should be filtered out of display
    assert "app.port" not in captured.out


def test_category_filter_structural(tmp_path, capsys):
    src = "app:\n  port: 80\n"
    dep = "app:\n  port: 80\n  debug: true\n"
    ns = _ns(tmp_path, src, dep, category="structural")
    _dispatch(ns)
    captured = capsys.readouterr()
    assert "debug" in captured.out


def test_add_classifier_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    _add_classifier_parser(sub)
    assert "classify" in sub._name_parser_map

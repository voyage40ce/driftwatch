"""Tests for driftwatch.commands.profiler_cmd."""
from __future__ import annotations

import argparse
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from driftwatch.commands.profiler_cmd import _dispatch
from driftwatch.profiler import EnvProfile, ProfilerError


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"profile_cmd": "capture", "env": "staging", "env_a": "dev", "env_b": "prod"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_capture_saves_and_returns_zero(tmp_path, monkeypatch):
    import driftwatch.profiler as mod
    monkeypatch.setattr(mod, "PROFILE_DIR", tmp_path / "profiles")
    ns = _ns(profile_cmd="capture", env="staging")
    result = _dispatch(ns)
    assert result == 0


def test_diff_no_changes_returns_zero():
    a = EnvProfile("dev", 0.0, {"x": 1})
    b = EnvProfile("prod", 1.0, {"x": 1})
    with patch("driftwatch.commands.profiler_cmd.load_profile", side_effect=[a, b]):
        ns = _ns(profile_cmd="diff", env_a="dev", env_b="prod")
        assert _dispatch(ns) == 0


def test_diff_with_changes_returns_one():
    a = EnvProfile("dev", 0.0, {"x": 1})
    b = EnvProfile("prod", 1.0, {"x": 2})
    with patch("driftwatch.commands.profiler_cmd.load_profile", side_effect=[a, b]):
        ns = _ns(profile_cmd="diff", env_a="dev", env_b="prod")
        assert _dispatch(ns) == 1


def test_diff_missing_profile_returns_two():
    with patch("driftwatch.commands.profiler_cmd.load_profile", side_effect=ProfilerError("No profile")):
        ns = _ns(profile_cmd="diff", env_a="ghost", env_b="prod")
        assert _dispatch(ns) == 2


def test_unknown_subcommand_returns_two():
    ns = _ns(profile_cmd="unknown")
    assert _dispatch(ns) == 2

"""Tests for driftwatch.commands.policy_cmd."""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from driftwatch.commands.policy_cmd import _dispatch


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"policy_cmd": None, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# validate sub-command
# ---------------------------------------------------------------------------

def test_validate_valid_policy_returns_zero(tmp_path: Path) -> None:
    p = _write(tmp_path, "policy.yaml", """
        env: production
        ignore:
          - pattern: "feature_flags.*"
    """)
    ns = _ns(policy_cmd="validate", policy=str(p))
    assert _dispatch(ns) == 0


def test_validate_missing_policy_returns_two(tmp_path: Path) -> None:
    ns = _ns(policy_cmd="validate", policy=str(tmp_path / "missing.yaml"))
    assert _dispatch(ns) == 2


def test_validate_invalid_yaml_returns_two(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(": : :")
    ns = _ns(policy_cmd="validate", policy=str(p))
    assert _dispatch(ns) == 2


# ---------------------------------------------------------------------------
# apply sub-command
# ---------------------------------------------------------------------------

def test_apply_no_drift_after_policy_returns_zero(tmp_path: Path) -> None:
    expected = _write(tmp_path, "expected.yaml", "key: value\nfeature_flags.dark_mode: 'true'\n")
    actual = _write(tmp_path, "actual.yaml", "key: value\nfeature_flags.dark_mode: 'false'\n")
    policy = _write(tmp_path, "policy.yaml", "ignore:\n  - pattern: \"feature_flags.*\"\n")
    ns = _ns(policy_cmd="apply", expected=str(expected), actual=str(actual), policy=str(policy))
    assert _dispatch(ns) == 0


def test_apply_drift_remains_returns_one(tmp_path: Path) -> None:
    expected = _write(tmp_path, "expected.yaml", "host: db-prod\nport: '5432'\n")
    actual = _write(tmp_path, "actual.yaml", "host: db-staging\nport: '5432'\n")
    policy = _write(tmp_path, "policy.yaml", "ignore: []\n")
    ns = _ns(policy_cmd="apply", expected=str(expected), actual=str(actual), policy=str(policy))
    assert _dispatch(ns) == 1


def test_apply_missing_config_returns_two(tmp_path: Path) -> None:
    policy = _write(tmp_path, "policy.yaml", "ignore: []\n")
    ns = _ns(
        policy_cmd="apply",
        expected=str(tmp_path / "nope.yaml"),
        actual=str(tmp_path / "nope2.yaml"),
        policy=str(policy),
    )
    assert _dispatch(ns) == 2


def test_apply_missing_policy_returns_two(tmp_path: Path) -> None:
    cfg = _write(tmp_path, "cfg.yaml", "a: 1\n")
    ns = _ns(
        policy_cmd="apply",
        expected=str(cfg),
        actual=str(cfg),
        policy=str(tmp_path / "missing.yaml"),
    )
    assert _dispatch(ns) == 2


def test_dispatch_unknown_subcmd_returns_one() -> None:
    ns = _ns(policy_cmd="nonexistent")
    assert _dispatch(ns) == 1

"""Tests for driftwatch.policy."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from driftwatch.differ import DriftReport
from driftwatch.policy import (
    Policy,
    PolicyError,
    PolicyRule,
    apply_policy,
    load_policy,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "policy.yaml"
    p.write_text(textwrap.dedent(content))
    return p


def _report(*keys: str) -> DriftReport:
    return DriftReport(changes={k: ("old", "new") for k in keys})


# ---------------------------------------------------------------------------
# load_policy
# ---------------------------------------------------------------------------

def test_load_policy_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(PolicyError, match="not found"):
        load_policy(tmp_path / "missing.yaml")


def test_load_policy_invalid_yaml_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(": : :")
    with pytest.raises(PolicyError, match="Invalid YAML"):
        load_policy(p)


def test_load_policy_non_mapping_raises(tmp_path: Path) -> None:
    p = _write(tmp_path, "- a\n- b\n")
    with pytest.raises(PolicyError, match="mapping"):
        load_policy(p)


def test_load_policy_empty_file_returns_empty_policy(tmp_path: Path) -> None:
    p = tmp_path / "empty.yaml"
    p.write_text("")
    policy = load_policy(p)
    assert policy.rules == []


def test_load_policy_parses_glob_rules(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        """
        env: staging
        ignore:
          - pattern: "feature_flags.*"
            reason: managed separately
        """,
    )
    policy = load_policy(p)
    assert policy.env == "staging"
    assert len(policy.rules) == 1
    assert policy.rules[0].pattern == "feature_flags.*"
    assert policy.rules[0].reason == "managed separately"


def test_load_policy_parses_regex_rules(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        """
        ignore:
          - pattern: "^build\\.id$"
            match_type: regex
        """,
    )
    policy = load_policy(p)
    assert policy.rules[0].match_type == "regex"


def test_load_policy_string_shorthand(tmp_path: Path) -> None:
    p = _write(tmp_path, "ignore:\n  - \"*.secret\"\n")
    policy = load_policy(p)
    assert policy.rules[0].pattern == "*.secret"
    assert policy.rules[0].match_type == "glob"


# ---------------------------------------------------------------------------
# PolicyRule.matches
# ---------------------------------------------------------------------------

def test_glob_rule_matches() -> None:
    rule = PolicyRule(pattern="feature_flags.*")
    assert rule.matches("feature_flags.dark_mode")
    assert not rule.matches("database.host")


def test_regex_rule_matches() -> None:
    rule = PolicyRule(pattern=r"^build\.id$", match_type="regex")
    assert rule.matches("build.id")
    assert not rule.matches("build.id.extra")


# ---------------------------------------------------------------------------
# apply_policy
# ---------------------------------------------------------------------------

def test_apply_policy_removes_matching_keys() -> None:
    policy = Policy(rules=[PolicyRule(pattern="feature_flags.*")])
    report = _report("feature_flags.dark_mode", "database.host")
    result = apply_policy(report, policy)
    assert "feature_flags.dark_mode" not in result.changes
    assert "database.host" in result.changes


def test_apply_policy_no_rules_returns_same_changes() -> None:
    policy = Policy()
    report = _report("a", "b")
    result = apply_policy(report, policy)
    assert set(result.changes) == {"a", "b"}


def test_apply_policy_all_filtered_returns_empty() -> None:
    policy = Policy(rules=[PolicyRule(pattern="*")])
    report = _report("x", "y", "z")
    result = apply_policy(report, policy)
    assert result.changes == {}

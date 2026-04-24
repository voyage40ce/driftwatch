"""Tests for driftwatch.pruner."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.pruner import (
    PruneRule,
    PrunerError,
    format_prune_summary,
    load_prune_rules,
    prune_report,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _report(*changes: dict) -> DriftReport:
    return DriftReport(changes=list(changes))


def _chg(key: str, change_type: str = "changed") -> dict:
    return {"key": key, "change_type": change_type, "old": "a", "new": "b"}


# ---------------------------------------------------------------------------
# load_prune_rules
# ---------------------------------------------------------------------------

def test_load_prune_rules_returns_list():
    rules = load_prune_rules([{"key_pattern": "db.*"}])
    assert len(rules) == 1
    assert rules[0].key_pattern == "db.*"


def test_load_prune_rules_missing_key_pattern_raises():
    with pytest.raises(PrunerError, match="key_pattern"):
        load_prune_rules([{"change_types": ["changed"]}])


def test_load_prune_rules_non_list_raises():
    with pytest.raises(PrunerError, match="list"):
        load_prune_rules({"key_pattern": "*"})


def test_load_prune_rules_non_dict_entry_raises():
    with pytest.raises(PrunerError, match="mapping"):
        load_prune_rules(["db.*"])


def test_load_prune_rules_invalid_change_types_raises():
    with pytest.raises(PrunerError, match="change_types"):
        load_prune_rules([{"key_pattern": "*", "change_types": "changed"}])


# ---------------------------------------------------------------------------
# prune_report
# ---------------------------------------------------------------------------

def test_prune_no_rules_keeps_all():
    report = _report(_chg("db.host"), _chg("app.port"))
    result = prune_report(report, [])
    assert result.kept_count == 2
    assert result.pruned_count == 0


def test_prune_glob_pattern_matches_key():
    report = _report(_chg("db.host"), _chg("app.port"))
    rules = [PruneRule(key_pattern="db.*")]
    result = prune_report(report, rules)
    assert result.pruned_count == 1
    assert result.pruned[0]["key"] == "db.host"
    assert result.kept_count == 1


def test_prune_change_type_filter_respected():
    report = _report(_chg("db.host", "changed"), _chg("db.port", "added"))
    rules = [PruneRule(key_pattern="db.*", change_types=["changed"])]
    result = prune_report(report, rules)
    assert result.pruned_count == 1
    assert result.pruned[0]["key"] == "db.host"
    assert result.kept[0]["key"] == "db.port"


def test_prune_wildcard_suppresses_all():
    report = _report(_chg("a"), _chg("b"), _chg("c"))
    rules = [PruneRule(key_pattern="*")]
    result = prune_report(report, rules)
    assert result.pruned_count == 3
    assert result.kept_count == 0


def test_prune_non_report_raises():
    with pytest.raises(PrunerError):
        prune_report({"changes": []}, [])


# ---------------------------------------------------------------------------
# format_prune_summary
# ---------------------------------------------------------------------------

def test_format_prune_summary_shows_counts():
    report = _report(_chg("db.host"))
    rules = [PruneRule(key_pattern="db.*")]
    result = prune_report(report, rules)
    summary = format_prune_summary(result)
    assert "Pruned : 1" in summary
    assert "Kept   : 0" in summary


def test_format_prune_summary_lists_suppressed_keys():
    report = _report(_chg("secret.token", "changed"))
    rules = [PruneRule(key_pattern="secret.*")]
    result = prune_report(report, rules)
    summary = format_prune_summary(result)
    assert "secret.token" in summary

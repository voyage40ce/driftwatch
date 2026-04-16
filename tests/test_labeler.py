"""Tests for driftwatch.labeler."""
from __future__ import annotations

import pytest
from pathlib import Path

import yaml

from driftwatch.labeler import (
    LabelError,
    LabelRule,
    apply_labels,
    load_label_rules,
)
from driftwatch.differ import DriftReport


def _write_rules(tmp_path: Path, rules: list) -> Path:
    p = tmp_path / "rules.yaml"
    p.write_text(yaml.dump({"rules": rules}))
    return p


def _report(changed=None, added=None, removed=None) -> DriftReport:
    return DriftReport(
        changed=changed or {},
        added=list(added or []),
        removed=list(removed or []),
    )


def test_load_label_rules_missing_file_raises(tmp_path):
    with pytest.raises(LabelError, match="not found"):
        load_label_rules(tmp_path / "nope.yaml")


def test_load_label_rules_invalid_yaml_raises(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(": : :")
    with pytest.raises(LabelError, match="Invalid YAML"):
        load_label_rules(p)


def test_load_label_rules_missing_rules_key_raises(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text(yaml.dump({"other": []}))
    with pytest.raises(LabelError, match="'rules' key"):
        load_label_rules(p)


def test_load_label_rules_unknown_severity_raises(tmp_path):
    p = _write_rules(tmp_path, [{"pattern": "*", "severity": "extreme"}])
    with pytest.raises(LabelError, match="Unknown severity"):
        load_label_rules(p)


def test_load_label_rules_returns_rules(tmp_path):
    p = _write_rules(tmp_path, [{"pattern": "db.*", "severity": "critical", "reason": "database"}])
    rules = load_label_rules(p)
    assert len(rules) == 1
    assert rules[0].severity == "critical"
    assert rules[0].pattern == "db.*"


def test_apply_labels_changed_key_matched(tmp_path):
    rules = [LabelRule(pattern="db.*", severity="critical", reason="db")]
    report = _report(changed={"db.host": ("old", "new")})
    labeled = apply_labels(report, rules)
    assert len(labeled) == 1
    assert labeled[0].severity == "critical"
    assert labeled[0].change_type == "changed"


def test_apply_labels_unmatched_defaults_to_info():
    rules = [LabelRule(pattern="db.*", severity="high")]
    report = _report(added=["app.port"])
    labeled = apply_labels(report, rules)
    assert labeled[0].severity == "info"


def test_apply_labels_removed_key():
    rules = [LabelRule(pattern="secret.*", severity="high", reason="secrets")]
    report = _report(removed=["secret.key"])
    labeled = apply_labels(report, rules)
    assert labeled[0].change_type == "removed"
    assert labeled[0].severity == "high"


def test_apply_labels_empty_report_returns_empty():
    labeled = apply_labels(_report(), [])
    assert labeled == []

"""Attach and query severity labels to drift keys based on pattern rules."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from driftwatch.differ import DriftReport


class LabelError(Exception):
    """Raised when label rules cannot be loaded or applied."""


SEVERITY_LEVELS = ("critical", "high", "medium", "low", "info")


@dataclass
class LabelRule:
    pattern: str
    severity: str
    reason: str = ""


@dataclass
class LabeledKey:
    key: str
    change_type: str  # changed | added | removed
    severity: str
    reason: str


def load_label_rules(path: str | Path) -> List[LabelRule]:
    """Load label rules from a YAML file."""
    p = Path(path)
    if not p.exists():
        raise LabelError(f"Label rules file not found: {path}")
    try:
        data = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        raise LabelError(f"Invalid YAML in label rules: {exc}") from exc
    if not isinstance(data, dict) or "rules" not in data:
        raise LabelError("Label rules file must contain a top-level 'rules' key")
    rules = []
    for item in data["rules"]:
        sev = item.get("severity", "info")
        if sev not in SEVERITY_LEVELS:
            raise LabelError(f"Unknown severity '{sev}' in label rules")
        rules.append(LabelRule(pattern=item["pattern"], severity=sev, reason=item.get("reason", "")))
    return rules


def _match_rule(key: str, rules: List[LabelRule]) -> Optional[LabelRule]:
    for rule in rules:
        if fnmatch.fnmatch(key, rule.pattern):
            return rule
    return None


def apply_labels(report: DriftReport, rules: List[LabelRule]) -> List[LabeledKey]:
    """Return a LabeledKey for every drifted key in *report*."""
    labeled: List[LabeledKey] = []
    default = LabelRule(pattern="*", severity="info")

    for key, (old, new) in report.changed.items():
        rule = _match_rule(key, rules) or default
        labeled.append(LabeledKey(key=key, change_type="changed", severity=rule.severity, reason=rule.reason))
    for key in report.added:
        rule = _match_rule(key, rules) or default
        labeled.append(LabeledKey(key=key, change_type="added", severity=rule.severity, reason=rule.reason))
    for key in report.removed:
        rule = _match_rule(key, rules) or default
        labeled.append(LabeledKey(key=key, change_type="removed", severity=rule.severity, reason=rule.reason))
    return labeled

"""classifier.py – classify drift report items by severity and category."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.differ import DriftReport


class ClassifierError(Exception):
    """Raised when classification fails."""


# Severity tiers (mirrors scorer.py conventions)
SEVERITY_NONE = "none"
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

_SENSITIVE_PATTERNS = ("password", "secret", "token", "key", "credential")


@dataclass
class ClassifiedItem:
    key: str
    change_type: str        # "changed" | "added" | "removed"
    severity: str
    category: str           # "security" | "structural" | "value"
    old_value: object = None
    new_value: object = None


@dataclass
class ClassifyResult:
    env: str
    items: List[ClassifiedItem] = field(default_factory=list)

    def by_severity(self, severity: str) -> List[ClassifiedItem]:
        return [i for i in self.items if i.severity == severity]

    def by_category(self, category: str) -> List[ClassifiedItem]:
        return [i for i in self.items if i.category == category]

    @property
    def has_high(self) -> bool:
        return any(i.severity == SEVERITY_HIGH for i in self.items)


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(p in lower for p in _SENSITIVE_PATTERNS)


def _classify_item(key: str, change_type: str, old, new) -> ClassifiedItem:
    if _is_sensitive(key):
        category = "security"
        severity = SEVERITY_HIGH
    elif change_type in ("added", "removed"):
        category = "structural"
        severity = SEVERITY_MEDIUM
    else:
        category = "value"
        old_str = str(old) if old is not None else ""
        new_str = str(new) if new is not None else ""
        severity = SEVERITY_LOW if old_str and new_str else SEVERITY_MEDIUM

    return ClassifiedItem(
        key=key,
        change_type=change_type,
        severity=severity,
        category=category,
        old_value=old,
        new_value=new,
    )


def classify(report: DriftReport) -> ClassifyResult:
    """Classify every change in *report* and return a ClassifyResult."""
    if not isinstance(report, DriftReport):
        raise ClassifierError("classify() requires a DriftReport instance")

    result = ClassifyResult(env=report.env)
    for change in report.changes:
        item = _classify_item(
            key=change.key,
            change_type=change.change_type,
            old=getattr(change, "old_value", None),
            new=getattr(change, "new_value", None),
        )
        result.items.append(item)
    return result


def format_classify_summary(result: ClassifyResult) -> str:
    lines = [f"Classification summary for env: {result.env}"]
    for sev in (SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_NONE):
        items = result.by_severity(sev)
        if items:
            lines.append(f"  [{sev.upper()}] {len(items)} item(s)")
            for i in items:
                lines.append(f"    - {i.key} ({i.change_type}, {i.category})")
    if not result.items:
        lines.append("  No drift items to classify.")
    return "\n".join(lines)

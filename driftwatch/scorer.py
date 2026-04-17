"""Drift severity scorer — assigns a numeric score to a DriftReport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from driftwatch.differ import DriftReport

# Weight per change type
_WEIGHTS: Dict[str, float] = {
    "changed": 1.0,
    "added": 0.5,
    "removed": 0.8,
}


class ScorerError(Exception):
    """Raised when scoring fails."""


@dataclass
class DriftScore:
    env: str
    total: float
    changed: int
    added: int
    removed: int
    severity: str  # "none" | "low" | "medium" | "high"


def _severity(score: float) -> str:
    if score == 0:
        return "none"
    if score < 2:
        return "low"
    if score < 5:
        return "medium"
    return "high"


def score_report(report: DriftReport) -> DriftScore:
    """Return a DriftScore for *report*."""
    changed = sum(1 for c in report.changes if c.change_type == "changed")
    added = sum(1 for c in report.changes if c.change_type == "added")
    removed = sum(1 for c in report.changes if c.change_type == "removed")

    total = (
        changed * _WEIGHTS["changed"]
        + added * _WEIGHTS["added"]
        + removed * _WEIGHTS["removed"]
    )

    return DriftScore(
        env=report.env,
        total=round(total, 2),
        changed=changed,
        added=added,
        removed=removed,
        severity=_severity(total),
    )


def format_score(ds: DriftScore) -> str:
    lines = [
        f"Env      : {ds.env}",
        f"Score    : {ds.total}",
        f"Severity : {ds.severity.upper()}",
        f"Changed  : {ds.changed}  Added: {ds.added}  Removed: {ds.removed}",
    ]
    return "\n".join(lines)

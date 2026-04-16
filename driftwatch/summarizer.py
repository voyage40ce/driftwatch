"""Summarize drift reports into human-readable statistics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from driftwatch.differ import DriftReport


class SummarizerError(Exception):
    """Raised when summarization fails."""


@dataclass
class DriftSummary:
    env: str
    total_keys: int
    changed: int
    added: int
    removed: int
    drift_score: float  # changed+added+removed / total_keys, 0.0-1.0
    top_changed: List[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return (self.changed + self.added + self.removed) > 0


def summarize(report: DriftReport, env: str = "unknown", top_n: int = 5) -> DriftSummary:
    """Produce a DriftSummary from a DriftReport.

    Args:
        report: A DriftReport produced by ``driftwatch.differ.diff``.
        env: A label identifying the environment (e.g. "production").
        top_n: Maximum number of drifted keys to include in ``top_changed``.

    Returns:
        A populated :class:`DriftSummary`.

    Raises:
        SummarizerError: If *report* is not a valid DriftReport instance.
    """
    if not isinstance(report, DriftReport):
        raise SummarizerError(
            f"Expected a DriftReport instance, got {type(report).__name__!r}"
        )

    changed = [k for k, c in report.changes.items() if c.get("type") == "changed"]
    added = [k for k, c in report.changes.items() if c.get("type") == "added"]
    removed = [k for k, c in report.changes.items() if c.get("type") == "removed"]

    total_drift = len(changed) + len(added) + len(removed)

    # total_keys: keys present in either side
    all_keys_set: set = set()
    for k, c in report.changes.items():
        all_keys_set.add(k)
    # also account for unchanged keys via source config if available
    total_keys = max(len(all_keys_set), total_drift)
    if hasattr(report, "source") and isinstance(report.source, dict):
        from driftwatch.differ import _flatten
        total_keys = max(len(_flatten(report.source)), total_drift)

    drift_score = round(total_drift / total_keys, 4) if total_keys else 0.0

    top_changed = sorted(changed + added + removed)[:top_n]

    return DriftSummary(
        env=env,
        total_keys=total_keys,
        changed=len(changed),
        added=len(added),
        removed=len(removed),
        drift_score=drift_score,
        top_changed=top_changed,
    )


def format_summary(summary: DriftSummary) -> str:
    """Return a formatted string representation of a DriftSummary."""
    lines = [
        f"Environment : {summary.env}",
        f"Total keys  : {summary.total_keys}",
        f"Changed     : {summary.changed}",
        f"Added       : {summary.added}",
        f"Removed     : {summary.removed}",
        f"Drift score : {summary.drift_score:.2%}",
    ]
    if summary.top_changed:
        lines.append("Top drifted : " + ", ".join(summary.top_changed))
    return "\n".join(lines)

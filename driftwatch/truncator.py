"""truncator.py – Truncate drift reports to a maximum number of changes.

Useful for large environments where only the first N drifted keys are
relevant for display or downstream processing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from driftwatch.differ import DriftReport


class TruncatorError(Exception):
    """Raised when truncation cannot be performed."""


@dataclass
class TruncateResult:
    env: str
    items: list = field(default_factory=list)
    total_before: int = 0
    truncated: bool = False

    @property
    def removed_count(self) -> int:
        return self.total_before - len(self.items)


def truncate_report(report: DriftReport, limit: int) -> TruncateResult:
    """Return a TruncateResult containing at most *limit* change items.

    Parameters
    ----------
    report:
        A :class:`~driftwatch.differ.DriftReport` produced by :func:`~driftwatch.differ.diff`.
    limit:
        Maximum number of change items to keep.  Must be >= 1.

    Raises
    ------
    TruncatorError
        If *report* is not a DriftReport or *limit* is less than 1.
    """
    if not isinstance(report, DriftReport):
        raise TruncatorError("report must be a DriftReport instance")
    if limit < 1:
        raise TruncatorError("limit must be >= 1")

    items = list(report.changes)
    total_before = len(items)
    kept = items[:limit]
    return TruncateResult(
        env=report.env,
        items=kept,
        total_before=total_before,
        truncated=total_before > limit,
    )


def format_truncate_summary(result: TruncateResult) -> str:
    """Return a human-readable summary line for a TruncateResult."""
    kept = len(result.items)
    if result.truncated:
        return (
            f"[{result.env}] Showing {kept} of {result.total_before} changes "
            f"({result.removed_count} truncated)"
        )
    return f"[{result.env}] {kept} change(s) – nothing truncated"

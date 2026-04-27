"""composer.py – Compose multiple DriftReports into a single unified report.

Useful when aggregating drift results from several environment pairs before
reporting, exporting, or auditing them together.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport


class ComposerError(Exception):
    """Raised when composition fails."""


@dataclass
class ComposeResult:
    """Result of composing multiple DriftReports."""

    env: str
    reports: List[DriftReport]
    changes: List[dict] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.changes)

    @property
    def report_count(self) -> int:
        return len(self.reports)


def compose_reports(
    reports: List[DriftReport],
    env: Optional[str] = None,
    deduplicate: bool = True,
) -> ComposeResult:
    """Merge a list of DriftReports into one ComposeResult.

    Args:
        reports: Non-empty list of DriftReport objects to merge.
        env: Optional label for the composed environment.  Defaults to
             the env of the first report.
        deduplicate: When True, changes with identical (key, change_type)
                     pairs from different reports are included only once.

    Returns:
        A ComposeResult containing all (de-duplicated) changes.

    Raises:
        ComposerError: If *reports* is empty or contains non-DriftReport items.
    """
    if not reports:
        raise ComposerError("compose_reports requires at least one DriftReport.")

    for idx, r in enumerate(reports):
        if not isinstance(r, DriftReport):
            raise ComposerError(
                f"Item at index {idx} is not a DriftReport: {type(r).__name__}"
            )

    resolved_env = env or reports[0].env
    seen: set = set()
    merged: List[dict] = []

    for report in reports:
        for change in report.changes:
            key = (change.get("key"), change.get("change_type"))
            if deduplicate and key in seen:
                continue
            seen.add(key)
            merged.append(change)

    return ComposeResult(env=resolved_env, reports=list(reports), changes=merged)


def format_compose_summary(result: ComposeResult) -> str:
    """Return a human-readable summary of a ComposeResult."""
    lines = [
        f"Composed environment : {result.env}",
        f"Source reports       : {result.report_count}",
        f"Total changes        : {len(result.changes)}",
        f"Has drift            : {result.has_drift}",
    ]
    return "\n".join(lines)

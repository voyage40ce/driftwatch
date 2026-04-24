"""Deduplicator: remove duplicate drift items across multiple DriftReports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from driftwatch.differ import DriftReport


class DeduplicatorError(Exception):
    """Raised when deduplication cannot be performed."""


@dataclass
class DeduplicateResult:
    """Result of deduplicating one or more DriftReports."""

    unique_changes: List[Tuple[str, str, object, object]] = field(default_factory=list)
    unique_added: List[Tuple[str, object]] = field(default_factory=list)
    unique_removed: List[Tuple[str, object]] = field(default_factory=list)
    duplicate_count: int = 0


def has_duplicates(result: DeduplicateResult) -> bool:
    """Return True if any duplicates were found during deduplication."""
    return result.duplicate_count > 0


def deduplicate(reports: List[DriftReport]) -> DeduplicateResult:
    """Merge multiple DriftReports, discarding identical duplicate items.

    Two items are considered duplicates when they share the same key and
    values (for changes) or the same key and value (for added/removed).

    Args:
        reports: One or more DriftReport instances to merge.

    Returns:
        A DeduplicateResult containing only unique drift items.

    Raises:
        DeduplicatorError: If *reports* is empty.
    """
    if not reports:
        raise DeduplicatorError("At least one DriftReport is required.")

    seen_changes: dict = {}
    seen_added: dict = {}
    seen_removed: dict = {}
    duplicate_count = 0

    for report in reports:
        for key, old, new in report.changes:
            token = (key, repr(old), repr(new))
            if token in seen_changes:
                duplicate_count += 1
            else:
                seen_changes[token] = (key, old, new)

        for key, value in report.added:
            token = (key, repr(value))
            if token in seen_added:
                duplicate_count += 1
            else:
                seen_added[token] = (key, value)

        for key, value in report.removed:
            token = (key, repr(value))
            if token in seen_removed:
                duplicate_count += 1
            else:
                seen_removed[token] = (key, value)

    return DeduplicateResult(
        unique_changes=list(seen_changes.values()),
        unique_added=list(seen_added.values()),
        unique_removed=list(seen_removed.values()),
        duplicate_count=duplicate_count,
    )


def format_dedup_summary(result: DeduplicateResult) -> str:
    """Return a human-readable summary of the deduplication result."""
    total = len(result.unique_changes) + len(result.unique_added) + len(result.unique_removed)
    lines = [
        f"Unique drift items : {total}",
        f"  changed          : {len(result.unique_changes)}",
        f"  added            : {len(result.unique_added)}",
        f"  removed          : {len(result.unique_removed)}",
        f"Duplicates removed : {result.duplicate_count}",
    ]
    return "\n".join(lines)

"""indexer.py — Build a searchable index of drift report items by key, type, and value.

Provides fast lookup of drift changes across large reports without
re-scanning the full change list each time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.differ import DriftReport


class IndexerError(Exception):
    """Raised when indexing fails."""


@dataclass
class IndexEntry:
    """A single entry in the drift index."""

    key: str
    change_type: str  # 'changed', 'added', 'removed'
    old_value: object
    new_value: object

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"IndexEntry(key={self.key!r}, change_type={self.change_type!r}, "
            f"old={self.old_value!r}, new={self.new_value!r})"
        )


@dataclass
class IndexResult:
    """The result of indexing a DriftReport."""

    env: str
    _by_key: Dict[str, IndexEntry] = field(default_factory=dict, repr=False)
    _by_type: Dict[str, List[IndexEntry]] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[IndexEntry]:
        """Return the IndexEntry for *key*, or ``None`` if not indexed."""
        return self._by_key.get(key)

    def by_type(self, change_type: str) -> List[IndexEntry]:
        """Return all entries whose ``change_type`` matches *change_type*."""
        return list(self._by_type.get(change_type, []))

    def search(self, pattern: str) -> List[IndexEntry]:
        """Return all entries whose key matches the regex *pattern*."""
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            raise IndexerError(f"Invalid search pattern {pattern!r}: {exc}") from exc
        return [e for k, e in self._by_key.items() if rx.search(k)]

    @property
    def all_entries(self) -> List[IndexEntry]:
        """Return every indexed entry in insertion order."""
        return list(self._by_key.values())

    @property
    def total(self) -> int:
        """Total number of indexed entries."""
        return len(self._by_key)


def build_index(report: DriftReport) -> IndexResult:
    """Build an :class:`IndexResult` from a :class:`~driftwatch.differ.DriftReport`.

    Parameters
    ----------
    report:
        The drift report to index.  Must be a :class:`DriftReport` instance.

    Returns
    -------
    IndexResult
        A fully populated index ready for querying.

    Raises
    ------
    IndexerError
        If *report* is not a :class:`DriftReport`.
    """
    if not isinstance(report, DriftReport):
        raise IndexerError(
            f"build_index expects a DriftReport, got {type(report).__name__!r}"
        )

    result = IndexResult(env=report.env)

    for item in report.changes:
        entry = IndexEntry(
            key=item.key,
            change_type=item.change_type,
            old_value=item.old_value,
            new_value=item.new_value,
        )
        result._by_key[item.key] = entry
        result._by_type.setdefault(item.change_type, []).append(entry)

    return result


def format_index_summary(result: IndexResult) -> str:
    """Return a human-readable summary of an :class:`IndexResult`."""
    lines: List[str] = [
        f"Index for env '{result.env}' — {result.total} entr{'y' if result.total == 1 else 'ies'}",
    ]
    for ctype in ("changed", "added", "removed"):
        entries = result.by_type(ctype)
        if entries:
            lines.append(f"  {ctype}: {len(entries)}")
            for e in entries:
                lines.append(f"    {e.key}")
    return "\n".join(lines)

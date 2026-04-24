"""grouper.py – group drift report items by a chosen dimension.

Supported dimensions: 'change_type', 'prefix' (first dot-segment of key),
or any arbitrary string prefix depth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

from driftwatch.differ import DriftReport


class GrouperError(Exception):
    """Raised when grouping cannot be performed."""


GroupBy = Literal["change_type", "prefix"]


@dataclass
class GroupResult:
    """Mapping from group label -> list of DriftReport items."""

    groups: Dict[str, List[dict]] = field(default_factory=dict)
    group_by: str = "change_type"

    def labels(self) -> List[str]:
        """Return sorted group labels."""
        return sorted(self.groups.keys())

    def count(self, label: str) -> int:
        return len(self.groups.get(label, []))

    def total(self) -> int:
        return sum(len(v) for v in self.groups.values())


def _prefix_of(key: str) -> str:
    """Return the first dot-segment of a flattened key, or the key itself."""
    return key.split(".")[0]


def group_report(report: DriftReport, group_by: GroupBy = "change_type") -> GroupResult:
    """Group all changes in *report* by the chosen dimension.

    Parameters
    ----------
    report:
        A :class:`~driftwatch.differ.DriftReport` produced by :func:`~driftwatch.differ.diff`.
    group_by:
        ``'change_type'`` groups by ``item['type']`` (added/removed/changed).
        ``'prefix'`` groups by the first segment of the dot-notation key.

    Returns
    -------
    GroupResult
    """
    if not isinstance(report, DriftReport):
        raise GrouperError("report must be a DriftReport instance")

    if group_by not in ("change_type", "prefix"):
        raise GrouperError(f"Unknown group_by value: {group_by!r}")

    groups: Dict[str, List[dict]] = {}

    for item in report.changes:
        if group_by == "change_type":
            label = item.get("type", "unknown")
        else:
            label = _prefix_of(item.get("key", ""))

        groups.setdefault(label, []).append(item)

    return GroupResult(groups=groups, group_by=group_by)


def format_group_summary(result: GroupResult) -> str:
    """Return a human-readable summary of grouped drift results."""
    if result.total() == 0:
        return "No drift detected – nothing to group."

    lines = [f"Grouped by '{result.group_by}' ({result.total()} total change(s)):\n"]
    for label in result.labels():
        items = result.groups[label]
        lines.append(f"  [{label}]  {len(items)} change(s)")
        for item in items:
            key = item.get("key", "?")
            change_type = item.get("type", "?")
            old = item.get("old_value", "")
            new = item.get("new_value", "")
            if change_type == "changed":
                lines.append(f"    - {key}: {old!r} -> {new!r}")
            elif change_type == "added":
                lines.append(f"    + {key}: {new!r}")
            else:
                lines.append(f"    x {key}: {old!r}")
    return "\n".join(lines)

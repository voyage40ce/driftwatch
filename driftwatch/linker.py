"""linker.py – link (cross-reference) two DriftReports by shared keys.

Given two DriftReport objects (e.g. from different environments), the linker
finds keys that appear in *both* reports and annotates whether their change
types agree or conflict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport


class LinkerError(Exception):
    """Raised when linking fails due to invalid input."""


@dataclass
class LinkedKey:
    key: str
    left_change_type: str   # "changed" | "added" | "removed"
    right_change_type: str
    agrees: bool            # True when both sides have the same change_type


@dataclass
class LinkResult:
    left_env: str
    right_env: str
    linked: List[LinkedKey] = field(default_factory=list)
    left_only: List[str] = field(default_factory=list)
    right_only: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return any(not lk.agrees for lk in self.linked)


def _key_type_map(report: DriftReport) -> dict:
    """Return {key: change_type} for every item in *report*."""
    return {item["key"]: item["change_type"] for item in report.changes}


def link_reports(
    left: DriftReport,
    right: DriftReport,
    left_env: str = "left",
    right_env: str = "right",
) -> LinkResult:
    """Cross-reference *left* and *right* DriftReports.

    Args:
        left: First DriftReport.
        right: Second DriftReport.
        left_env: Human-readable name for the left environment.
        right_env: Human-readable name for the right environment.

    Returns:
        A :class:`LinkResult` describing shared and exclusive keys.

    Raises:
        LinkerError: If either argument is not a DriftReport.
    """
    if not isinstance(left, DriftReport) or not isinstance(right, DriftReport):
        raise LinkerError("Both arguments must be DriftReport instances.")

    left_map = _key_type_map(left)
    right_map = _key_type_map(right)

    shared_keys = set(left_map) & set(right_map)
    result = LinkResult(left_env=left_env, right_env=right_env)

    for key in sorted(shared_keys):
        lct = left_map[key]
        rct = right_map[key]
        result.linked.append(LinkedKey(key=key, left_change_type=lct, right_change_type=rct, agrees=(lct == rct)))

    result.left_only = sorted(set(left_map) - shared_keys)
    result.right_only = sorted(set(right_map) - shared_keys)

    return result


def format_link_summary(result: LinkResult) -> str:
    """Return a human-readable summary of a :class:`LinkResult`."""
    lines = [
        f"Link: {result.left_env} <-> {result.right_env}",
        f"  Shared keys  : {len(result.linked)}",
        f"  Conflicts    : {sum(1 for lk in result.linked if not lk.agrees)}",
        f"  Left-only    : {len(result.left_only)}",
        f"  Right-only   : {len(result.right_only)}",
    ]
    if result.linked:
        lines.append("  Details:")
        for lk in result.linked:
            status = "OK" if lk.agrees else "CONFLICT"
            lines.append(f"    [{status}] {lk.key}  ({result.left_env}={lk.left_change_type}, {result.right_env}={lk.right_change_type})")
    return "\n".join(lines)

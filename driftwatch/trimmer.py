"""trimmer.py – remove drift items that fall below a severity threshold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from driftwatch.differ import DriftReport
from driftwatch.scorer import _severity


class TrimmerError(Exception):
    """Raised when trimming configuration is invalid."""


SEVERITY_ORDER = ["none", "low", "medium", "high"]


@dataclass
class TrimOptions:
    min_severity: str = "low"  # inclusive lower bound
    include_types: Optional[List[str]] = None  # e.g. ["changed", "added", "removed"]


def _severity_index(level: str) -> int:
    try:
        return SEVERITY_ORDER.index(level.lower())
    except ValueError:
        raise TrimmerError(f"Unknown severity level: {level!r}")


def trim_report(report: DriftReport, opts: TrimOptions) -> DriftReport:
    """Return a new DriftReport containing only items that meet *opts* criteria."""
    min_idx = _severity_index(opts.min_severity)

    kept = []
    for item in report.changes:
        sev = _severity(item)
        if _severity_index(sev) < min_idx:
            continue
        if opts.include_types and item.get("type") not in opts.include_types:
            continue
        kept.append(item)

    return DriftReport(
        env=report.env,
        source=report.source,
        changes=kept,
    )


def format_trim_summary(original: DriftReport, trimmed: DriftReport) -> str:
    removed = len(original.changes) - len(trimmed.changes)
    lines = [
        f"Trim summary for env={trimmed.env!r}",
        f"  Original items : {len(original.changes)}",
        f"  After trim     : {len(trimmed.changes)}",
        f"  Removed        : {removed}",
    ]
    return "\n".join(lines)

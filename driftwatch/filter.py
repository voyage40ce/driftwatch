"""Key-path filtering for drift reports."""
from __future__ import annotations
import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport, DriftItem


class FilterError(Exception):
    pass


@dataclass
class FilterOptions:
    include: List[str] = field(default_factory=list)  # glob patterns to include
    exclude: List[str] = field(default_factory=list)  # glob patterns to exclude
    changed_only: bool = False
    added_only: bool = False
    removed_only: bool = False


def _matches_any(key: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(key, p) for p in patterns)


def _keep(item: DriftItem, opts: FilterOptions) -> bool:
    key = item.key
    if opts.include and not _matches_any(key, opts.include):
        return False
    if opts.exclude and _matches_any(key, opts.exclude):
        return False
    if opts.changed_only and item.kind != "changed":
        return False
    if opts.added_only and item.kind != "added":
        return False
    if opts.removed_only and item.kind != "removed":
        return False
    return True


def filter_report(report: DriftReport, opts: Optional[FilterOptions] = None) -> DriftReport:
    """Return a new DriftReport containing only items that pass the filter."""
    if opts is None:
        return report
    kept = [item for item in report.items if _keep(item, opts)]
    return DriftReport(items=kept, env=report.env)

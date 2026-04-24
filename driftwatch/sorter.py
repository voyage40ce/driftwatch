"""sorter.py – sort drift report items by various criteria."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from driftwatch.differ import DriftReport

SortKey = Literal["key", "change_type", "severity"]
SortOrder = Literal["asc", "desc"]

_CHANGE_TYPE_ORDER = {"changed": 0, "added": 1, "removed": 2}
_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}


class SorterError(Exception):
    """Raised when sorting cannot be completed."""


@dataclass
class SortOptions:
    key: SortKey = "key"
    order: SortOrder = "asc"
    severity_map: Optional[dict] = None  # key -> severity string, from scorer


def _item_sort_key(item: dict, opts: SortOptions):
    """Return a comparable sort key for a single diff item."""
    if opts.key == "key":
        return item.get("key", "")
    if opts.key == "change_type":
        ct = item.get("change_type", "changed")
        return _CHANGE_TYPE_ORDER.get(ct, 99)
    if opts.key == "severity":
        sev_map = opts.severity_map or {}
        sev = sev_map.get(item.get("key", ""), "none")
        return _SEVERITY_ORDER.get(sev, 99)
    raise SorterError(f"Unknown sort key: {opts.key!r}")


def sort_report(report: DriftReport, opts: Optional[SortOptions] = None) -> DriftReport:
    """Return a new DriftReport with items sorted according to *opts*.

    The original report is not mutated.
    """
    if not isinstance(report, DriftReport):
        raise SorterError("sort_report expects a DriftReport instance")

    if opts is None:
        opts = SortOptions()

    reverse = opts.order == "desc"

    try:
        sorted_items = sorted(
            report.items,
            key=lambda item: _item_sort_key(item, opts),
            reverse=reverse,
        )
    except Exception as exc:  # pragma: no cover
        raise SorterError(f"Sorting failed: {exc}") from exc

    return DriftReport(
        env=report.env,
        source=report.source,
        deployed=report.deployed,
        items=sorted_items,
    )


def format_sort_summary(report: DriftReport, opts: SortOptions) -> str:
    """Return a human-readable one-liner describing the sort applied."""
    count = len(report.items)
    return (
        f"{count} item(s) sorted by '{opts.key}' "
        f"({'descending' if opts.order == 'desc' else 'ascending'})"
    )

"""Export drift reports to various output formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import Literal

from driftwatch.differ import DriftReport


class ExportError(Exception):
    """Raised when a report cannot be exported."""


OutputFormat = Literal["json", "csv"]


@dataclass
class ExportOptions:
    fmt: OutputFormat = "json"
    indent: int = 2
    include_unchanged: bool = False


def _report_to_records(report: DriftReport) -> list[dict]:
    """Convert a DriftReport into a flat list of row dicts."""
    rows: list[dict] = []
    for key, (old, new) in report.changed.items():
        rows.append({"key": key, "status": "changed", "old": old, "new": new})
    for key, value in report.added.items():
        rows.append({"key": key, "status": "added", "old": "", "new": value})
    for key, value in report.removed.items():
        rows.append({"key": key, "status": "removed", "old": value, "new": ""})
    return rows


def export_json(report: DriftReport, opts: ExportOptions) -> str:
    """Serialise *report* as a JSON string."""
    payload = {
        "has_drift": report.has_drift,
        "changed": {
            k: {"old": o, "new": n} for k, (o, n) in report.changed.items()
        },
        "added": report.added,
        "removed": report.removed,
    }
    return json.dumps(payload, indent=opts.indent, default=str)


def export_csv(report: DriftReport, opts: ExportOptions) -> str:  # noqa: ARG001
    """Serialise *report* as a CSV string."""
    rows = _report_to_records(report)
    if not rows:
        return "key,status,old,new\n"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["key", "status", "old", "new"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def export_report(report: DriftReport, opts: ExportOptions | None = None) -> str:
    """Export *report* using *opts*. Raises :class:`ExportError` on unknown format."""
    if opts is None:
        opts = ExportOptions()
    if opts.fmt == "json":
        return export_json(report, opts)
    if opts.fmt == "csv":
        return export_csv(report, opts)
    raise ExportError(f"Unknown export format: {opts.fmt!r}")

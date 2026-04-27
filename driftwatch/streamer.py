"""streamer.py – Stream drift reports as newline-delimited JSON (NDJSON)."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import IO, Iterable, Iterator

from driftwatch.differ import DriftReport


class StreamerError(Exception):
    """Raised when streaming fails."""


@dataclass
class StreamOptions:
    pretty: bool = False
    include_clean: bool = True
    indent: int = 2


def _report_to_record(report: DriftReport) -> dict:
    """Convert a DriftReport to a plain dict suitable for JSON serialisation."""
    changes = [
        {"key": c.key, "change_type": c.change_type, "old": c.old_value, "new": c.new_value}
        for c in report.changes
    ]
    return {
        "env": report.env,
        "has_drift": report.has_drift,
        "change_count": len(changes),
        "changes": changes,
    }


def stream_reports(
    reports: Iterable[DriftReport],
    options: StreamOptions | None = None,
    out: IO[str] | None = None,
) -> Iterator[str]:
    """Yield each report as a JSON string and optionally write to *out*."""
    if options is None:
        options = StreamOptions()
    if out is None:
        out = sys.stdout

    for report in reports:
        if not options.include_clean and not report.has_drift:
            continue
        record = _report_to_record(report)
        if options.pretty:
            line = json.dumps(record, indent=options.indent)
        else:
            line = json.dumps(record, separators=(",", ":"))
        out.write(line + "\n")
        yield line


def stream_to_file(reports: Iterable[DriftReport], path: str, options: StreamOptions | None = None) -> int:
    """Write all reports to *path* as NDJSON.  Returns the number of lines written."""
    count = 0
    try:
        with open(path, "w", encoding="utf-8") as fh:
            for _ in stream_reports(reports, options=options, out=fh):
                count += 1
    except OSError as exc:
        raise StreamerError(f"Cannot write stream to {path!r}: {exc}") from exc
    return count

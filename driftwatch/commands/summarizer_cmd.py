"""CLI sub-command: summarize drift reports.

Usage:
    driftwatch summarize <source> <deployed>
    driftwatch summarize <source> <deployed> --json
    driftwatch summarize <source> <deployed> --min-severity medium

Exit codes:
    0 – no drift detected
    1 – drift detected
    2 – error (missing file, bad YAML, etc.)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.summarizer import SummarizerError, summarize, format_summary

if TYPE_CHECKING:
    pass


_SEVERITY_LEVELS = ("none", "low", "medium", "high")


def _add_summarizer_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'summarize' sub-command."""
    p = subparsers.add_parser(
        "summarize",
        help="Summarize drift between a source-of-truth and a deployed config.",
    )
    p.add_argument("source", help="Path to the source-of-truth YAML file.")
    p.add_argument("deployed", help="Path to the deployed environment YAML file.")
    p.add_argument(
        "--env",
        default="deployed",
        metavar="NAME",
        help="Environment label used in the summary (default: 'deployed').",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output the summary as JSON instead of human-readable text.",
    )
    p.add_argument(
        "--min-severity",
        dest="min_severity",
        choices=_SEVERITY_LEVELS,
        default="none",
        help="Only report drift at or above this severity level (default: none).",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    """Entry point called by the CLI router."""
    # Load both configs.
    try:
        source_cfg, deployed_cfg = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # Compute the drift report.
    report = diff(ns.env, source_cfg, deployed_cfg)

    # Build the summary.
    try:
        summary = summarize(report)
    except SummarizerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # Apply min-severity filter when requested.
    if ns.min_severity != "none":
        min_idx = _SEVERITY_LEVELS.index(ns.min_severity)
        # Filter changes below the requested severity.
        # summarize() already groups by severity; we just gate the exit code
        # and output on the effective drift after filtering.
        severity_order = {s: i for i, s in enumerate(_SEVERITY_LEVELS)}
        filtered_changes = [
            c for c in report.changes
            if severity_order.get(getattr(c, "severity", "low"), 1) >= min_idx
        ]
        report = type(report)(report.env, filtered_changes)
        try:
            summary = summarize(report)
        except SummarizerError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    # Emit output.
    if ns.as_json:
        payload = {
            "env": summary.env,
            "has_drift": summary.has_drift,
            "total": summary.total,
            "added": summary.added,
            "removed": summary.removed,
            "changed": summary.changed,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_summary(summary))

    return 1 if summary.has_drift else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Public registration hook consumed by commands/__init__.py."""
    _add_summarizer_parser(subparsers)

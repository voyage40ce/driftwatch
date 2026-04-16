"""CLI sub-command: label — apply severity labels to drift keys."""
from __future__ import annotations

import argparse
import sys

from driftwatch.labeler import LabelError, apply_labels, load_label_rules
from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.reporter import ReportOptions, format_report


def _add_labeler_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("label", help="Apply severity labels to drifted keys")
    p.add_argument("source", help="Source-of-truth YAML file")
    p.add_argument("deployed", help="Deployed environment YAML file")
    p.add_argument("--rules", required=True, metavar="FILE", help="Label rules YAML file")
    p.add_argument("--min-severity", default="info", choices=["critical", "high", "medium", "low", "info"],
                   help="Only show keys at or above this severity")
    p.set_defaults(func=_dispatch)


_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        source, deployed = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    try:
        rules = load_label_rules(ns.rules)
    except LabelError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    report = diff(source, deployed)
    labeled = apply_labels(report, rules)

    min_rank = _SEVERITY_ORDER[ns.min_severity]
    visible = [lk for lk in labeled if _SEVERITY_ORDER[lk.severity] <= min_rank]

    if not visible:
        print("No labeled drift above minimum severity threshold.")
        return 0

    for lk in visible:
        reason_str = f"  # {lk.reason}" if lk.reason else ""
        print(f"[{lk.severity.upper():8s}] {lk.change_type:7s}  {lk.key}{reason_str}")

    return 1 if report.has_drift else 0


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_labeler_parser(subparsers)

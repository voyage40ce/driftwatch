"""classifier_cmd.py – CLI sub-command: driftwatch classify."""
from __future__ import annotations

import argparse
import sys

from driftwatch.classifier import ClassifyResult, classify, format_classify_summary
from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff


def _add_classifier_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "classify",
        help="Classify drift items by severity and category",
    )
    p.add_argument("source", help="Path to source-of-truth YAML")
    p.add_argument("deployed", help="Path to deployed config YAML")
    p.add_argument(
        "--env",
        default="default",
        help="Environment name label (default: 'default')",
    )
    p.add_argument(
        "--min-severity",
        choices=("low", "medium", "high"),
        default=None,
        help="Only show items at or above this severity",
    )
    p.add_argument(
        "--category",
        choices=("security", "structural", "value"),
        default=None,
        help="Filter output to a specific category",
    )


_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        source, deployed = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    report = diff(source, deployed, env=ns.env)
    result = classify(report)

    items = result.items
    if ns.category:
        items = [i for i in items if i.category == ns.category]
    if ns.min_severity:
        min_idx = _SEVERITY_ORDER[ns.min_severity]
        items = [i for i in items if _SEVERITY_ORDER.get(i.severity, -1) >= min_idx]

    from driftwatch.classifier import ClassifyResult as CR
    filtered = CR(env=result.env)
    filtered.items = items

    print(format_classify_summary(filtered))
    return 1 if result.has_high else (0 if not items else 0)


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_classifier_parser(subparsers)
    subparsers._name_parser_map["classify"].set_defaults(func=_dispatch)

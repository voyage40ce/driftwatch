"""CLI sub-command: driftwatch filter"""
from __future__ import annotations
import argparse
import sys

from driftwatch.loader import load_pair, ConfigLoadError
from driftwatch.differ import diff
from driftwatch.filter import FilterOptions, filter_report
from driftwatch.reporter import ReportOptions, print_report


def _add_filter_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("filter", help="Diff two configs and filter the results")
    p.add_argument("source", help="Source-of-truth YAML")
    p.add_argument("deployed", help="Deployed config YAML")
    p.add_argument("--include", nargs="+", default=[], metavar="PATTERN",
                   help="Glob patterns for keys to include")
    p.add_argument("--exclude", nargs="+", default=[], metavar="PATTERN",
                   help="Glob patterns for keys to exclude")
    p.add_argument("--changed-only", action="store_true")
    p.add_argument("--added-only", action="store_true")
    p.add_argument("--removed-only", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        source, deployed = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = diff(source, deployed)
    opts = FilterOptions(
        include=ns.include,
        exclude=ns.exclude,
        changed_only=ns.changed_only,
        added_only=ns.added_only,
        removed_only=ns.removed_only,
    )
    filtered = filter_report(report, opts)
    ropts = ReportOptions(color=not ns.no_color)
    print_report(filtered, ropts)
    return 1 if filtered.items else 0


def register(sub: argparse._SubParsersAction) -> None:
    _add_filter_parser(sub)

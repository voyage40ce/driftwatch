"""CLI sub-command: driftwatch scope <scope-file> <scope-name> <deployed> <source>"""
from __future__ import annotations

import argparse
import sys

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.reporter import ReportOptions, format_report
from driftwatch.scoper import ScopeError, apply_scope, load_scope


def _add_scoper_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "scope",
        help="Diff two configs restricted to a named scope of keys",
    )
    p.add_argument("scope_file", help="YAML file containing scope definitions")
    p.add_argument("scope_name", help="Name of the scope to apply")
    p.add_argument("deployed", help="Deployed config YAML")
    p.add_argument("source", help="Source-of-truth config YAML")
    p.add_argument("--no-color", action="store_true", help="Disable coloured output")
    p.add_argument("--env", default="", help="Environment label for the report")


def _dispatch(ns: argparse.Namespace) -> int:
    # Load scope definition
    try:
        scope = load_scope(ns.scope_file, ns.scope_name)
    except ScopeError as exc:
        print(f"[scope error] {exc}", file=sys.stderr)
        return 2

    # Load config pair and diff
    try:
        deployed, source = load_pair(ns.deployed, ns.source)
    except ConfigLoadError as exc:
        print(f"[load error] {exc}", file=sys.stderr)
        return 2

    report = diff(deployed, source, env=ns.env or ns.deployed)

    # Apply scope filter
    result = apply_scope(report, scope)

    opts = ReportOptions(color=not ns.no_color)
    print(format_report(result.report, opts))
    print(
        f"Scope '{scope.name}': {result.total_after} of {result.total_before} "
        f"change(s) shown ({result.filtered_count} filtered)."
    )

    return 1 if result.report.changes else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    _add_scoper_parser(subparsers)
    subparsers._name_parser_map["scope"].set_defaults(func=_dispatch)  # noqa: SLF001

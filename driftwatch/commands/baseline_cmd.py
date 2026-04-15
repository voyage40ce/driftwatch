"""CLI sub-commands for baseline management.

Registers: baseline save, baseline load (diff), baseline list, baseline delete.
Intended to be wired into the main argparse parser in cli.py.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, _SubParsersAction
from typing import Sequence

from driftwatch.baseline import BaselineError, delete_baseline, list_baselines, load_baseline, save_baseline
from driftwatch.differ import diff, has_drift
from driftwatch.loader import ConfigLoadError, load_yaml
from driftwatch.reporter import ReportOptions, print_report


def _add_baseline_parser(subparsers: _SubParsersAction) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "baseline", help="Manage config baselines"
    )
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    # baseline save <name> <file>
    save_p = sub.add_parser("save", help="Save a YAML file as a named baseline")
    save_p.add_argument("name", help="Baseline name")
    save_p.add_argument("file", help="Path to YAML config file")

    # baseline diff <name> <file>
    diff_p = sub.add_parser("diff", help="Diff a YAML file against a saved baseline")
    diff_p.add_argument("name", help="Baseline name to compare against")
    diff_p.add_argument("file", help="Path to current YAML config file")
    diff_p.add_argument("--no-color", action="store_true", default=False)

    # baseline list
    sub.add_parser("list", help="List saved baselines")

    # baseline delete <name>
    del_p = sub.add_parser("delete", help="Delete a named baseline")
    del_p.add_argument("name", help="Baseline name to delete")


def _cmd_save(args) -> int:  # type: ignore[no-untyped-def]
    try:
        config = load_yaml(args.file)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    path = save_baseline(args.name, config)
    print(f"Baseline '{args.name}' saved to {path}")
    return 0


def _cmd_diff(args) -> int:  # type: ignore[no-untyped-def]
    try:
        baseline_config = load_baseline(args.name)
        current_config = load_yaml(args.file)
    except (BaselineError, ConfigLoadError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = diff(baseline_config, current_config)
    opts = ReportOptions(color=not args.no_color)
    print_report(report, opts)
    return 1 if has_drift(report) else 0


def _cmd_list() -> int:
    names = list_baselines()
    if not names:
        print("No baselines saved.")
    else:
        for name in names:
            print(name)
    return 0


def _cmd_delete(args) -> int:  # type: ignore[no-untyped-def]
    try:
        delete_baseline(args.name)
    except BaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Baseline '{args.name}' deleted.")
    return 0


def run_baseline_command(args) -> int:  # type: ignore[no-untyped-def]
    """Dispatch to the appropriate baseline sub-command."""
    dispatch = {
        "save": lambda: _cmd_save(args),
        "diff": lambda: _cmd_diff(args),
        "list": _cmd_list,
        "delete": lambda: _cmd_delete(args),
    }
    handler = dispatch.get(args.baseline_cmd)
    if handler is None:
        print(f"Unknown baseline command: {args.baseline_cmd}", file=sys.stderr)
        return 2
    return handler()

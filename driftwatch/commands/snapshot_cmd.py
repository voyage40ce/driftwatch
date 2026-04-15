"""CLI sub-commands for snapshot management."""
from __future__ import annotations

import argparse
import sys

from driftwatch.loader import load_yaml, ConfigLoadError
from driftwatch.snapshot import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    SnapshotError,
)
from driftwatch.differ import diff
from driftwatch.reporter import format_report, print_report, ReportOptions


def _add_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'snapshot' sub-command group."""
    parser = subparsers.add_parser("snapshot", help="Manage environment snapshots")
    sub = parser.add_subparsers(dest="snapshot_cmd", required=True)

    # snapshot save
    p_save = sub.add_parser("save", help="Capture a snapshot of a config file")
    p_save.add_argument("name", help="Snapshot name / label")
    p_save.add_argument("config", help="Path to YAML config file")
    p_save.add_argument("--dir", dest="snap_dir", default=None,
                        help="Directory to store snapshots (default: .driftwatch/snapshots)")

    # snapshot diff
    p_diff = sub.add_parser("diff", help="Diff a snapshot against a config file")
    p_diff.add_argument("name", help="Snapshot name to compare")
    p_diff.add_argument("config", help="Path to current YAML config file")
    p_diff.add_argument("--dir", dest="snap_dir", default=None)
    p_diff.add_argument("--no-color", action="store_true", default=False)

    # snapshot list
    p_list = sub.add_parser("list", help="List saved snapshots")
    p_list.add_argument("--dir", dest="snap_dir", default=None)

    parser.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    """Route to the correct snapshot sub-command handler."""
    handlers = {
        "save": _cmd_save,
        "diff": _cmd_diff,
        "list": _cmd_list,
    }
    handler = handlers.get(args.snapshot_cmd)
    if handler is None:
        print(f"Unknown snapshot sub-command: {args.snapshot_cmd}", file=sys.stderr)
        return 2
    return handler(args)


def _cmd_save(args: argparse.Namespace) -> int:
    try:
        config = load_yaml(args.config)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    kwargs = {"snap_dir": args.snap_dir} if args.snap_dir else {}
    try:
        path = save_snapshot(args.name, config, **kwargs)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Snapshot '{args.name}' saved to {path}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    kwargs = {"snap_dir": args.snap_dir} if args.snap_dir else {}
    try:
        snapshot_data = load_snapshot(args.name, **kwargs)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        current = load_yaml(args.config)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = diff(snapshot_data["config"], current)
    opts = ReportOptions(color=not args.no_color)
    print_report(report, opts)
    return 1 if report.has_drift else 0


def _cmd_list(args: argparse.Namespace) -> int:
    kwargs = {"snap_dir": args.snap_dir} if args.snap_dir else {}
    try:
        snapshots = list_snapshots(**kwargs)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not snapshots:
        print("No snapshots found.")
        return 0

    print(f"{'Name':<30} {'Saved At':<25} File")
    print("-" * 75)
    for s in snapshots:
        print(f"{s['name']:<30} {s.get('saved_at', 'unknown'):<25} {s.get('source', '')}")
    return 0

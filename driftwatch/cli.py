"""Command-line interface for driftwatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from driftwatch.differ import diff
from driftwatch.loader import ConfigLoadError, load_pair, load_yaml
from driftwatch.reporter import ReportOptions, print_report
from driftwatch.snapshot import SnapshotError, list_snapshots, load_snapshot, save_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driftwatch",
        description="Detect configuration drift between YAML files or snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- diff command ---
    diff_cmd = sub.add_parser("diff", help="Compare two YAML config files.")
    diff_cmd.add_argument("source", help="Source-of-truth YAML file.")
    diff_cmd.add_argument("deployed", help="Deployed environment YAML file.")
    diff_cmd.add_argument(
        "--no-color", action="store_true", help="Disable coloured output."
    )
    diff_cmd.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0, even when drift is detected.",
    )

    # --- snapshot save ---
    snap_save = sub.add_parser("snapshot-save", help="Save a config snapshot.")
    snap_save.add_argument("name", help="Snapshot name.")
    snap_save.add_argument("file", help="YAML file to snapshot.")

    # --- snapshot diff ---
    snap_diff = sub.add_parser(
        "snapshot-diff", help="Diff a YAML file against a saved snapshot."
    )
    snap_diff.add_argument("name", help="Snapshot name to compare against.")
    snap_diff.add_argument("deployed", help="Deployed environment YAML file.")
    snap_diff.add_argument("--no-color", action="store_true")
    snap_diff.add_argument("--exit-zero", action="store_true")

    # --- snapshot list ---
    sub.add_parser("snapshot-list", help="List saved snapshots.")

    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        try:
            source, deployed = load_pair(args.source, args.deployed)
        except ConfigLoadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(2)
        report = diff(source, deployed)
        opts = ReportOptions(color=not args.no_color)
        print_report(report, opts)
        if report.has_drift and not args.exit_zero:
            sys.exit(1)

    elif args.command == "snapshot-save":
        try:
            config = load_yaml(Path(args.file))
        except ConfigLoadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(2)
        path = save_snapshot(config, args.name)
        print(f"Snapshot '{args.name}' saved to {path}")

    elif args.command == "snapshot-diff":
        try:
            source = load_snapshot(args.name)
            deployed = load_yaml(Path(args.deployed))
        except (SnapshotError, ConfigLoadError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(2)
        report = diff(source, deployed)
        opts = ReportOptions(color=not args.no_color)
        print_report(report, opts)
        if report.has_drift and not args.exit_zero:
            sys.exit(1)

    elif args.command == "snapshot-list":
        names = list_snapshots()
        if names:
            print("\n".join(names))
        else:
            print("No snapshots found.")


if __name__ == "__main__":  # pragma: no cover
    main()

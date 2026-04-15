"""CLI sub-command: driftwatch watch."""

from __future__ import annotations

import argparse
import sys
import logging

from driftwatch.watcher import WatchOptions, WatchError, watch
from driftwatch.reporter import ReportOptions, print_report

logger = logging.getLogger(__name__)


def _add_watch_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watch",
        help="Continuously poll two config files for drift.",
    )
    p.add_argument("source", help="Path to the source-of-truth YAML file.")
    p.add_argument("deployed", help="Path to the deployed config YAML file.")
    p.add_argument(
        "--interval",
        type=float,
        default=30.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 30).",
    )
    p.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        default=False,
        help="Disable coloured output.",
    )
    p.add_argument(
        "--iterations",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N iterations (useful for testing).",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    report_opts = ReportOptions(color=not ns.no_color)

    def on_drift(report):
        print_report(report, report_opts)

    def on_clear():
        print("[driftwatch] Drift cleared — configs are back in sync.")

    opts = WatchOptions(
        source=ns.source,
        deployed=ns.deployed,
        interval=ns.interval,
        max_iterations=ns.iterations,
        on_drift=on_drift,
        on_clear=on_clear,
    )

    try:
        watch(opts)
    except WatchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n[driftwatch] Watch stopped.", file=sys.stderr)

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_watch_parser(subparsers)

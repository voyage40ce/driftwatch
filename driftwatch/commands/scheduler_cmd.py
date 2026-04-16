"""CLI sub-command: driftwatch schedule."""
from __future__ import annotations

import argparse
import sys
from typing import List

from driftwatch.scheduler import ScheduleOptions, run_scheduler
from driftwatch.differ import DriftReport
from driftwatch.reporter import ReportOptions, print_report
from driftwatch.watcher import WatchError


def _add_scheduler_parser(subparsers) -> None:
    p = subparsers.add_parser("schedule", help="Run drift checks on a schedule")
    p.add_argument("source", help="Source-of-truth YAML")
    p.add_argument("deployed", help="Deployed config YAML")
    p.add_argument("--env", default="default", help="Environment label")
    p.add_argument("--interval", type=float, default=60.0, help="Seconds between checks")
    p.add_argument("--max-runs", type=int, default=None, help="Stop after N runs")
    p.add_argument("--no-color", action="store_true", help="Disable color output")
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    ropts = ReportOptions(color=not ns.no_color)

    def on_drift(report: DriftReport) -> None:
        print_report(report, ropts)

    def on_clear(report: DriftReport) -> None:
        print("[driftwatch] Drift resolved.")

    def on_error(exc: Exception) -> None:
        print(f"[driftwatch] Error: {exc}", file=sys.stderr)

    opts = ScheduleOptions(
        source=ns.source,
        deployed=ns.deployed,
        env=ns.env,
        interval=ns.interval,
        max_runs=ns.max_runs,
        on_drift=on_drift,
        on_clear=on_clear,
        on_error=on_error,
    )

    try:
        run_scheduler(opts)
    except Exception as exc:
        print(f"[driftwatch] Fatal: {exc}", file=sys.stderr)
        return 2

    return 0


def register(subparsers) -> None:
    _add_scheduler_parser(subparsers)

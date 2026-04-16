"""Scheduled drift checks with configurable cron-like intervals."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from driftwatch.watcher import WatchOptions, _load_and_diff, WatchError
from driftwatch.audit import record
from driftwatch.differ import DriftReport


class SchedulerError(Exception):
    """Raised when the scheduler encounters a fatal error."""


@dataclass
class ScheduleOptions:
    source: str
    deployed: str
    env: str
    interval: float = 60.0
    max_runs: Optional[int] = None
    on_drift: Callable[[DriftReport], None] = field(default=lambda r: None)
    on_clear: Callable[[DriftReport], None] = field(default=lambda r: None)
    on_error: Callable[[Exception], None] = field(default=lambda e: None)


def _run_once(opts: ScheduleOptions) -> DriftReport:
    watch_opts = WatchOptions(
        source=opts.source,
        deployed=opts.deployed,
        interval=opts.interval,
    )
    report = _load_and_diff(watch_opts)
    record(opts.env, report)
    return report


def run_scheduler(opts: ScheduleOptions, stop_event: Optional[threading.Event] = None) -> None:
    """Run scheduled drift checks until stop_event is set or max_runs reached."""
    if stop_event is None:
        stop_event = threading.Event()

    runs = 0
    last_had_drift: Optional[bool] = None

    while not stop_event.is_set():
        try:
            report = _run_once(opts)
            if report.has_drift:
                opts.on_drift(report)
            elif last_had_drift:
                opts.on_clear(report)
            last_had_drift = report.has_drift
        except WatchError as exc:
            opts.on_error(exc)
        except Exception as exc:
            opts.on_error(exc)

        runs += 1
        if opts.max_runs is not None and runs >= opts.max_runs:
            break

        stop_event.wait(timeout=opts.interval)

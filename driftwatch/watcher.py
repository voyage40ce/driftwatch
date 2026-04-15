"""Periodic drift watcher that polls configs and reports changes."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from driftwatch.loader import load_pair, ConfigLoadError
from driftwatch.differ import diff, DriftReport, has_drift

logger = logging.getLogger(__name__)


@dataclass
class WatchOptions:
    source: str
    deployed: str
    interval: float = 30.0
    max_iterations: Optional[int] = None
    on_drift: Callable[[DriftReport], None] = field(
        default_factory=lambda: lambda r: None
    )
    on_clear: Callable[[], None] = field(default_factory=lambda: lambda: None)


class WatchError(Exception):
    """Raised when the watcher encounters a fatal error."""


def _load_and_diff(source: str, deployed: str) -> DriftReport:
    """Load both configs and return a DriftReport."""
    try:
        src_cfg, dep_cfg = load_pair(source, deployed)
    except ConfigLoadError as exc:
        raise WatchError(str(exc)) from exc
    return diff(src_cfg, dep_cfg)


def watch(opts: WatchOptions) -> None:
    """Poll for drift between *source* and *deployed* configs.

    Calls ``opts.on_drift`` whenever drift is detected and ``opts.on_clear``
    when a previously drifted state becomes clean.  Runs until
    ``opts.max_iterations`` is reached (``None`` means run forever).
    """
    previous_drift: bool = False
    iteration = 0

    while opts.max_iterations is None or iteration < opts.max_iterations:
        try:
            report = _load_and_diff(opts.source, opts.deployed)
        except WatchError as exc:
            logger.error("watcher error: %s", exc)
            time.sleep(opts.interval)
            iteration += 1
            continue

        current_drift = has_drift(report)

        if current_drift:
            logger.debug("drift detected (%d changes)", len(report.changes))
            opts.on_drift(report)
        elif previous_drift and not current_drift:
            logger.debug("drift cleared")
            opts.on_clear()

        previous_drift = current_drift
        iteration += 1

        if opts.max_iterations is None or iteration < opts.max_iterations:
            time.sleep(opts.interval)

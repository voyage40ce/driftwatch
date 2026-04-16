"""Notification backends for drift events."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Callable, Optional

from driftwatch.differ import DriftReport


class NotifyError(Exception):
    """Raised when a notification cannot be delivered."""


@dataclass
class NotifyOptions:
    webhook_url: Optional[str] = None
    env: str = "unknown"
    extra_headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 5


def _build_payload(report: DriftReport, env: str) -> dict:
    """Build a JSON-serialisable payload from a DriftReport."""
    return {
        "env": env,
        "has_drift": report.has_drift,
        "changed": [
            {"key": k, "expected": e, "actual": a}
            for k, (e, a) in report.changed.items()
        ],
        "added": list(report.added.keys()),
        "removed": list(report.removed.keys()),
    }


def send_webhook(report: DriftReport, opts: NotifyOptions) -> None:
    """POST a drift report to a webhook URL.

    Raises NotifyError on any delivery failure.
    """
    if not opts.webhook_url:
        raise NotifyError("webhook_url is required")

    payload = json.dumps(_build_payload(report, opts.env)).encode()
    headers = {"Content-Type": "application/json", **opts.extra_headers}
    req = urllib.request.Request(
        opts.webhook_url, data=payload, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=opts.timeout):
            pass
    except urllib.error.URLError as exc:
        raise NotifyError(f"Webhook delivery failed: {exc}") from exc


def notify_if_drift(
    report: DriftReport,
    opts: NotifyOptions,
    sender: Callable[[DriftReport, NotifyOptions], None] = send_webhook,
) -> bool:
    """Call *sender* only when *report* contains drift.

    Returns True if a notification was sent, False otherwise.
    """
    if not report.has_drift:
        return False
    sender(report, opts)
    return True

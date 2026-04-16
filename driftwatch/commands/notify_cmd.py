"""CLI sub-command: notify — send drift report to a webhook."""

from __future__ import annotations

import argparse
import sys

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.notifier import NotifyError, NotifyOptions, notify_if_drift


def _add_notify_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "notify",
        help="Diff two configs and POST the result to a webhook.",
    )
    p.add_argument("expected", help="Path to the expected (source-of-truth) YAML.")
    p.add_argument("actual", help="Path to the actual (deployed) YAML.")
    p.add_argument(
        "--webhook",
        required=True,
        metavar="URL",
        help="Webhook URL to POST the drift report to.",
    )
    p.add_argument(
        "--env",
        default="unknown",
        help="Environment label included in the payload (default: unknown).",
    )
    p.add_argument(
        "--only-drift",
        action="store_true",
        default=False,
        help="Only send notification when drift is detected (default: always send).",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    """Load configs, diff them, and dispatch a webhook notification."""
    try:
        expected, actual = load_pair(ns.expected, ns.actual)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = diff(expected, actual)
    opts = NotifyOptions(webhook_url=ns.webhook, env=ns.env)

    if ns.only_drift and not report.has_drift:
        print("No drift detected — notification skipped.")
        return 0

    try:
        notify_if_drift(report, opts) if ns.only_drift else __import__(
            "driftwatch.notifier", fromlist=["send_webhook"]
        ).send_webhook(report, opts)
    except NotifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    status = "drift detected" if report.has_drift else "no drift"
    print(f"Notification sent ({status}).")
    return 1 if report.has_drift else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    _add_notify_parser(subparsers)

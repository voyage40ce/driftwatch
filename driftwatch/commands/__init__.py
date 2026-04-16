"""Register all sub-command modules with the top-level CLI parser."""
from __future__ import annotations

import argparse

from driftwatch.commands import (
    baseline_cmd,
    snapshot_cmd,
    watch_cmd,
    audit_cmd,
    policy_cmd,
    notify_cmd,
    scheduler_cmd,
    diffstore_cmd,
)


def register_all(subparsers: argparse._SubParsersAction) -> None:
    baseline_cmd.register(subparsers)
    snapshot_cmd._add_snapshot_parser(subparsers)
    watch_cmd.register(subparsers)
    audit_cmd.register(subparsers)
    policy_cmd.register(subparsers)
    notify_cmd.register(subparsers)
    scheduler_cmd.register(subparsers)
    diffstore_cmd.register(subparsers)

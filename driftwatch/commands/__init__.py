"""Register all CLI sub-commands."""
from driftwatch.commands import (
    baseline_cmd,
    snapshot_cmd,
    watch_cmd,
    audit_cmd,
    policy_cmd,
    notify_cmd,
    scheduler_cmd,
)


def register_all(subparsers) -> None:
    baseline_cmd.register(subparsers)
    snapshot_cmd.register(subparsers)
    watch_cmd.register(subparsers)
    audit_cmd.register(subparsers)
    policy_cmd.register(subparsers)
    notify_cmd.register(subparsers)
    scheduler_cmd.register(subparsers)

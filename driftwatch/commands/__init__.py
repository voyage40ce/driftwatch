"""CLI command modules for driftwatch."""
from __future__ import annotations

from driftwatch.commands.baseline_cmd import register as register_baseline
from driftwatch.commands.snapshot_cmd import _add_snapshot_parser


def register_all(subparsers) -> None:  # type: ignore[type-arg]
    """Register every available command group with *subparsers*."""
    register_baseline(subparsers)
    _add_snapshot_parser(subparsers)


__all__ = ["register_all", "register_baseline", "_add_snapshot_parser"]

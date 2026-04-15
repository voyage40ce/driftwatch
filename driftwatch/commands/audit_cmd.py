"""CLI sub-commands for the audit log (``driftwatch audit …``)."""

from __future__ import annotations

import argparse
import sys
from typing import List

from driftwatch.audit import AuditEntry, AuditError, load_entries


def _add_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    audit_p = subparsers.add_parser("audit", help="Manage the drift audit log")
    sub = audit_p.add_subparsers(dest="audit_cmd", metavar="COMMAND")

    # --- list ---
    list_p = sub.add_parser("list", help="Show recorded drift events")
    list_p.add_argument(
        "--drift-only",
        action="store_true",
        help="Show only events where drift was detected",
    )
    list_p.add_argument(
        "--label",
        metavar="LABEL",
        help="Filter by label",
    )
    list_p.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N entries (0 = all)",
    )

    audit_p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    cmd = getattr(ns, "audit_cmd", None)
    if cmd == "list" or cmd is None:
        return _cmd_list(ns)
    print(f"Unknown audit sub-command: {cmd}", file=sys.stderr)
    return 2


def _cmd_list(ns: argparse.Namespace) -> int:
    try:
        entries: List[AuditEntry] = load_entries()
    except AuditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not entries:
        print("No audit entries found.")
        return 0

    # Apply filters
    drift_only: bool = getattr(ns, "drift_only", False)
    label_filter: str | None = getattr(ns, "label", None)
    limit: int = getattr(ns, "limit", 0)

    if drift_only:
        entries = [e for e in entries if e.has_drift]
    if label_filter:
        entries = [e for e in entries if e.label == label_filter]
    if limit and limit > 0:
        entries = entries[-limit:]

    if not entries:
        print("No matching audit entries.")
        return 0

    for entry in entries:
        _print_entry(entry)

    return 0


def _print_entry(entry: AuditEntry) -> None:
    drift_marker = "[DRIFT]" if entry.has_drift else "[OK]   "
    label_str = f" ({entry.label})" if entry.label else ""
    print(f"{drift_marker} {entry.timestamp}{label_str}")
    print(f"         source  : {entry.source_file}")
    print(f"         deployed: {entry.deployed_file}")
    if entry.changed:
        print(f"         changed : {', '.join(entry.changed)}")
    if entry.added:
        print(f"         added   : {', '.join(entry.added)}")
    if entry.removed:
        print(f"         removed : {', '.join(entry.removed)}")


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    _add_audit_parser(subparsers)

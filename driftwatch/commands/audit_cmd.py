"""CLI sub-commands for the audit log (list, clear)."""
from __future__ import annotations

import argparse
from datetime import datetime

from driftwatch.audit import AuditError, list_entries, clear_entries, _audit_path


def _add_audit_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("audit", help="Manage the drift audit log")
    sub = p.add_subparsers(dest="audit_cmd", required=True)

    # list
    ls = sub.add_parser("list", help="Print recorded audit entries")
    ls.add_argument("--limit", type=int, default=20, help="Max entries to show (default 20)")
    ls.add_argument("--env", default=None, help="Filter by environment name")

    # clear
    sub.add_parser("clear", help="Delete all audit log entries")

    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> int:
    if args.audit_cmd == "list":
        return _cmd_list(args)
    if args.audit_cmd == "clear":
        return _cmd_clear(args)
    return 1


def _cmd_list(args: argparse.Namespace) -> int:
    try:
        entries = list_entries(env=args.env, limit=args.limit)
    except AuditError as exc:
        print(f"[audit] error: {exc}")
        return 2

    if not entries:
        print("No audit entries found.")
        return 0

    for entry in entries:
        _print_entry(entry)
    return 0


def _print_entry(entry: dict) -> None:
    ts = entry.get("timestamp", "?")
    env = entry.get("env", "?")
    drift = entry.get("has_drift", False)
    status = "DRIFT" if drift else "OK"
    changes = entry.get("change_count", 0)
    print(f"[{ts}] env={env} status={status} changes={changes}")


def _cmd_clear(args: argparse.Namespace) -> int:  # noqa: ARG001
    try:
        removed = clear_entries()
    except AuditError as exc:
        print(f"[audit] error: {exc}")
        return 2
    print(f"Cleared {removed} audit entries.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_audit_parser(subparsers)

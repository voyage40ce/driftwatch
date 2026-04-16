"""CLI sub-commands for diffstore: list and clear historical diffs."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from driftwatch.diffstore import load_diffs, clear_diffs, DEFAULT_DIR


def _add_diffstore_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("diffstore", help="Manage stored diff history")
    sub = p.add_subparsers(dest="diffstore_cmd", required=True)

    ls = sub.add_parser("list", help="List stored diffs for an environment")
    ls.add_argument("env", help="Environment name")
    ls.add_argument("--limit", type=int, default=20, help="Max entries to show")
    ls.add_argument("--dir", dest="store_dir", default=None, help="Custom store directory")

    cl = sub.add_parser("clear", help="Clear stored diffs for an environment")
    cl.add_argument("env", help="Environment name")
    cl.add_argument("--dir", dest="store_dir", default=None, help="Custom store directory")


def _dispatch(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.store_dir) if ns.store_dir else DEFAULT_DIR
    if ns.diffstore_cmd == "list":
        return _cmd_list(ns, base_dir)
    if ns.diffstore_cmd == "clear":
        return _cmd_clear(ns, base_dir)
    return 2


def _cmd_list(ns: argparse.Namespace, base_dir: Path) -> int:
    entries = load_diffs(ns.env, limit=ns.limit, base_dir=base_dir)
    if not entries:
        print(f"No stored diffs for environment '{ns.env}'.")
        return 0
    for e in entries:
        ts = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        status = "DRIFT" if e.has_drift else "clean"
        print(f"[{ts}] {e.env} — {status} ({len(e.changes)} change(s))")
    return 0


def _cmd_clear(ns: argparse.Namespace, base_dir: Path) -> int:
    count = clear_diffs(ns.env, base_dir=base_dir)
    print(f"Cleared {count} diff record(s) for '{ns.env}'.")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_diffstore_parser(subparsers)

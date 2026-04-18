"""CLI sub-commands for the archiver feature."""
from __future__ import annotations

import argparse
from typing import List

from driftwatch.archiver import archive_report, load_archives, clear_archives
from driftwatch.loader import load_pair, ConfigLoadError
from driftwatch.differ import diff


def _add_archiver_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("archive", help="Manage drift report archives")
    s = p.add_subparsers(dest="archive_cmd", required=True)

    save = s.add_parser("save", help="Archive a drift report for an environment")
    save.add_argument("source", help="Source-of-truth YAML")
    save.add_argument("deployed", help="Deployed config YAML")
    save.add_argument("--env", required=True, help="Environment name")

    ls = s.add_parser("list", help="List archived reports")
    ls.add_argument("--env", default=None, help="Filter by environment")
    ls.add_argument("--limit", type=int, default=20)

    clr = s.add_parser("clear", help="Delete archived reports")
    clr.add_argument("--env", default=None, help="Filter by environment")


def _dispatch(ns: argparse.Namespace) -> int:
    cmd = ns.archive_cmd
    if cmd == "save":
        return _cmd_save(ns)
    if cmd == "list":
        return _cmd_list(ns)
    if cmd == "clear":
        return _cmd_clear(ns)
    return 2


def _cmd_save(ns: argparse.Namespace) -> int:
    try:
        src, dep = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"error: {exc}")
        return 2
    report = diff(src, dep)
    archived = archive_report(report, env=ns.env)
    status = "drift" if report.has_drift else "clean"
    print(f"archived [{status}] {ns.env} -> {archived.path}")
    return 1 if report.has_drift else 0


def _cmd_list(ns: argparse.Namespace) -> int:
    entries = load_archives(env=ns.env)
    if not entries:
        print("no archives found")
        return 0
    for e in entries[-ns.limit:]:
        flag = "DRIFT" if e.has_drift else "clean"
        print(f"{e.env:20s}  {e.timestamp:.0f}  [{flag}]  changes={len(e.changes)}")
    return 0


def _cmd_clear(ns: argparse.Namespace) -> int:
    removed = clear_archives(env=ns.env)
    print(f"removed {removed} archive(s)")
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    _add_archiver_parser(sub)

"""CLI sub-commands for config pinning."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from driftwatch.loader import ConfigLoadError, load_yaml
from driftwatch.pinner import PinnerError, delete_pin, list_pins, load_pin, pin_config


def _add_pinner_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("pin", help="Manage pinned config baselines")
    s = p.add_subparsers(dest="pin_cmd", required=True)

    sv = s.add_parser("save", help="Pin current config for an env")
    sv.add_argument("env")
    sv.add_argument("config_file")
    sv.add_argument("--note", default="")

    s.add_parser("list", help="List pinned envs")

    sh = s.add_parser("show", help="Show pinned config for an env")
    sh.add_argument("env")

    d = s.add_parser("delete", help="Delete a pin")
    d.add_argument("env")

    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    if ns.pin_cmd == "save":
        return _cmd_save(ns)
    if ns.pin_cmd == "list":
        return _cmd_list(ns)
    if ns.pin_cmd == "show":
        return _cmd_show(ns)
    if ns.pin_cmd == "delete":
        return _cmd_delete(ns)
    return 1


def _cmd_save(ns: argparse.Namespace) -> int:
    try:
        cfg = load_yaml(Path(ns.config_file))
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    entry = pin_config(ns.env, cfg, note=ns.note)
    print(f"Pinned '{ns.env}' at {entry.pinned_at:.0f}")
    return 0


def _cmd_list(ns: argparse.Namespace) -> int:
    pins = list_pins()
    if not pins:
        print("No pins saved.")
    else:
        for env in pins:
            print(env)
    return 0


def _cmd_show(ns: argparse.Namespace) -> int:
    try:
        entry = load_pin(ns.env)
    except PinnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    import json
    print(json.dumps(entry.config, indent=2))
    return 0


def _cmd_delete(ns: argparse.Namespace) -> int:
    removed = delete_pin(ns.env)
    if not removed:
        print(f"No pin for '{ns.env}'.", file=sys.stderr)
        return 2
    print(f"Deleted pin for '{ns.env}'.")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_pinner_parser(sub)

"""CLI sub-command: aliaser – apply or list key aliases."""
from __future__ import annotations

import argparse
import sys
from typing import List

from driftwatch.aliaser import AliasError, load_alias_map, apply_aliases
from driftwatch.loader import ConfigLoadError, load_yaml


def _add_aliaser_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("aliaser", help="Apply or list key aliases.")
    sub = p.add_subparsers(dest="aliaser_cmd", required=True)

    ap = sub.add_parser("apply", help="Print config with aliased keys.")
    ap.add_argument("config", help="Path to config YAML file.")
    ap.add_argument("alias_file", help="Path to alias map YAML file.")

    lp = sub.add_parser("list", help="List all defined aliases.")
    lp.add_argument("alias_file", help="Path to alias map YAML file.")


def _cmd_apply(ns: argparse.Namespace) -> int:
    try:
        config = load_yaml(ns.config)
        alias_map = load_alias_map(ns.alias_file)
    except (ConfigLoadError, AliasError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    from driftwatch.differ import _flatten
    flat = _flatten(config)
    aliased = apply_aliases(flat, alias_map)
    for k, v in sorted(aliased.items()):
        print(f"  {k}: {v}")
    return 0


def _cmd_list(ns: argparse.Namespace) -> int:
    try:
        alias_map = load_alias_map(ns.alias_file)
    except AliasError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    aliases = alias_map.all_aliases()
    if not aliases:
        print("No aliases defined.")
        return 0
    print(f"{'Key':<40} {'Alias':<40}")
    print("-" * 80)
    for key, alias in sorted(aliases.items()):
        print(f"{key:<40} {alias:<40}")
    return 0


def _dispatch(ns: argparse.Namespace) -> int:
    if ns.aliaser_cmd == "apply":
        return _cmd_apply(ns)
    if ns.aliaser_cmd == "list":
        return _cmd_list(ns)
    return 1


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_aliaser_parser(subparsers)

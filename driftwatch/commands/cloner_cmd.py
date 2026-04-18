"""CLI sub-command: driftwatch clone."""
from __future__ import annotations

import argparse
import sys
from typing import List

from driftwatch.cloner import ClonerError, clone_from_file, format_clone_summary
from driftwatch.loader import load_yaml, ConfigLoadError
import driftwatch.loader as _loader
import yaml


def _add_cloner_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("clone", help="Clone a config to a new environment")
    p.add_argument("source_file", help="Path to source YAML config")
    p.add_argument("source_env", help="Name of the source environment")
    p.add_argument("target_env", help="Name of the target environment")
    p.add_argument(
        "--out",
        metavar="FILE",
        help="Write cloned config to FILE (default: stdout)",
    )
    p.add_argument(
        "--set",
        dest="overrides",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Override a key in the cloned config (dot notation)",
    )


def _parse_overrides(raw: List[str]) -> dict:
    result = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}': expected KEY=VALUE")
        k, v = item.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        overrides = _parse_overrides(ns.overrides)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    try:
        result = clone_from_file(
            ns.source_file, ns.source_env, ns.target_env, overrides or None
        )
    except ClonerError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    serialized = yaml.dump(result.config, default_flow_style=False)

    if ns.out:
        try:
            with open(ns.out, "w") as fh:
                fh.write(serialized)
        except OSError as exc:
            print(f"[error] could not write output file: {exc}", file=sys.stderr)
            return 2
    else:
        print(serialized, end="")

    print(format_clone_summary(result), file=sys.stderr)
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    _add_cloner_parser(subparsers)
    subparsers.choices["clone"].set_defaults(func=_dispatch)

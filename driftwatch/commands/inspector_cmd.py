"""inspector_cmd.py – CLI sub-command: driftwatch inspect."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from driftwatch.inspector import InspectorError, format_inspect, inspect_config
from driftwatch.loader import ConfigLoadError, load_yaml


def _add_inspector_parser(sub: "argparse._SubParsersAction") -> None:  # type: ignore[type-arg]
    p = sub.add_parser("inspect", help="Inspect fields in a config file")
    p.add_argument("config", help="Path to YAML config file")
    p.add_argument("--env", default="unknown", help="Environment label")
    p.add_argument(
        "--show-values",
        action="store_true",
        help="Print non-secret field values",
    )
    p.add_argument(
        "--secrets-only",
        action="store_true",
        help="Only list secret fields",
    )
    p.add_argument(
        "--min-depth",
        type=int,
        default=0,
        metavar="N",
        help="Only show fields at depth >= N",
    )


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        cfg = load_yaml(ns.config)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = inspect_config(cfg, env=ns.env)
    except InspectorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # Apply optional filters
    if ns.secrets_only:
        result.fields = [f for f in result.fields if f.is_secret]
    if ns.min_depth > 0:
        result.fields = [f for f in result.fields if f.depth >= ns.min_depth]

    print(format_inspect(result, show_values=ns.show_values))
    return 0


def register(sub: "argparse._SubParsersAction") -> None:  # type: ignore[type-arg]
    _add_inspector_parser(sub)
    sub.choices["inspect"].set_defaults(func=_dispatch)

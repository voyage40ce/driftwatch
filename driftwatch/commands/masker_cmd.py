"""CLI sub-command: driftwatch mask <config.yaml> [options]"""
from __future__ import annotations

import argparse
import sys

from driftwatch.loader import ConfigLoadError, load_yaml
from driftwatch.masker import MaskOptions, MaskerError, format_mask_summary, mask_config


def _add_masker_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("mask", help="Mask sensitive values in a config file")
    p.add_argument("config", help="Path to the YAML config file")
    p.add_argument(
        "--placeholder",
        default="***",
        help="Replacement string for masked values (default: ***)",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        metavar="REGEX",
        help="Additional regex pattern to treat as sensitive (repeatable)",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Match patterns case-sensitively",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary of masked keys instead of the full config",
    )
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        config = load_yaml(ns.config)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    extra_patterns: list[str] = ns.patterns or []
    opts = MaskOptions(
        patterns=MaskOptions().patterns + extra_patterns,
        placeholder=ns.placeholder,
        case_sensitive=ns.case_sensitive,
    )

    try:
        result = mask_config(config, opts)
    except MaskerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if ns.summary:
        print(format_mask_summary(result))
    else:
        import yaml  # local import to keep startup fast
        print(yaml.dump(result.config, default_flow_style=False), end="")
        if result.mask_count:
            print(f"# {result.mask_count} sensitive key(s) masked", file=sys.stderr)

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_masker_parser(subparsers)

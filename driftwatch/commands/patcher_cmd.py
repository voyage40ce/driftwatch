"""CLI sub-command: driftwatch patch"""
from __future__ import annotations

import argparse
import sys

import yaml

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.patcher import PatcherError, format_patch_summary, patch_config


def _add_patcher_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("patch", help="Patch a deployed config to match source-of-truth")
    p.add_argument("source", help="Source-of-truth YAML file")
    p.add_argument("deployed", help="Deployed config YAML file")
    p.add_argument("--output", "-o", default="-", help="Output file (default: stdout)")
    p.add_argument("--skip", nargs="*", default=[], metavar="KEY", help="Keys to skip")
    p.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        source, deployed = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    report = diff(source, deployed)

    try:
        result = patch_config(
            deployed,
            report,
            skip_keys=ns.skip,
            dry_run=ns.dry_run,
        )
    except PatcherError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    print(format_patch_summary(result))

    if ns.dry_run:
        return 0

    out_yaml = yaml.dump(result.patched, default_flow_style=False)
    if ns.output == "-":
        print(out_yaml)
    else:
        with open(ns.output, "w") as fh:
            fh.write(out_yaml)

    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_patcher_parser(sub)

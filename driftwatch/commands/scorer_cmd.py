"""CLI sub-command: driftwatch score <source> <deployed>"""
from __future__ import annotations

import argparse
import sys

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.scorer import ScorerError, format_score, score_report


def _add_scorer_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("score", help="Score drift severity between two config files")
    p.add_argument("source", help="Source-of-truth YAML")
    p.add_argument("deployed", help="Deployed environment YAML")
    p.add_argument("--env", default="default", help="Environment name")
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        source, deployed = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    try:
        report = diff(source, deployed, env=ns.env)
        ds = score_report(report)
    except ScorerError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    print(format_score(ds))
    return 1 if ds.total > 0 else 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_scorer_parser(sub)

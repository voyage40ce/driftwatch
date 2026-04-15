"""CLI sub-commands for policy management: validate and apply."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff, has_drift
from driftwatch.policy import PolicyError, apply_policy, load_policy
from driftwatch.reporter import ReportOptions, format_report


def _add_policy_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("policy", help="validate and apply drift-ignore policies")
    sp = p.add_subparsers(dest="policy_cmd", required=True)

    # validate
    val = sp.add_parser("validate", help="check a policy file for syntax errors")
    val.add_argument("policy", help="path to policy YAML file")

    # apply
    app = sp.add_parser("apply", help="diff two configs and apply a policy to the result")
    app.add_argument("expected", help="source-of-truth config YAML")
    app.add_argument("actual", help="deployed config YAML")
    app.add_argument("policy", help="path to policy YAML file")
    app.add_argument("--no-color", action="store_true", help="disable coloured output")

    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    if ns.policy_cmd == "validate":
        return _cmd_validate(ns)
    if ns.policy_cmd == "apply":
        return _cmd_apply(ns)
    return 1


def _cmd_validate(ns: argparse.Namespace) -> int:
    try:
        policy = load_policy(ns.policy)
    except PolicyError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    rule_count = len(policy.rules)
    print(f"Policy valid — env={policy.env!r}, {rule_count} rule(s)")
    return 0


def _cmd_apply(ns: argparse.Namespace) -> int:
    try:
        expected, actual = load_pair(ns.expected, ns.actual)
    except ConfigLoadError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    try:
        policy = load_policy(ns.policy)
    except PolicyError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    report = diff(expected, actual)
    filtered = apply_policy(report, policy)

    opts = ReportOptions(color=not getattr(ns, "no_color", False))
    print(format_report(filtered, opts))
    return 1 if has_drift(filtered) else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_policy_parser(subparsers)

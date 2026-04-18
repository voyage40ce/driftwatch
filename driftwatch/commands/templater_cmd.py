"""CLI sub-command: template — render a config template with variables."""
from __future__ import annotations

import argparse
import sys

import yaml

from driftwatch.templater import TemplaterError, load_template, render_template


def _add_templater_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("template", help="Render a config template")
    p.add_argument("template", help="Path to template YAML file")
    p.add_argument(
        "--var",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        dest="vars",
        help="Variable substitution (repeatable)",
    )
    p.add_argument(
        "--out",
        metavar="PATH",
        default=None,
        help="Write rendered output to file (default: stdout)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any variables are unresolved",
    )
    p.set_defaults(func=_dispatch)


def _parse_vars(var_list: list[str]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for item in var_list:
        if "=" not in item:
            raise ValueError(f"Invalid --var format (expected KEY=VALUE): {item!r}")
        k, _, v = item.partition("=")
        variables[k.strip()] = v
    return variables


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        variables = _parse_vars(ns.vars)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    try:
        tmpl = load_template(ns.template)
    except TemplaterError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    result = render_template(tmpl, variables)

    if result.unresolved:
        print(f"[warn] Unresolved variables: {', '.join(sorted(result.unresolved))}", file=sys.stderr)
        if ns.strict:
            return 2

    rendered_yaml = yaml.dump(result.rendered, default_flow_style=False)

    if ns.out:
        try:
            from pathlib import Path
            Path(ns.out).write_text(rendered_yaml)
            print(f"[ok] Rendered template written to {ns.out}")
        except OSError as exc:
            print(f"[error] Could not write output: {exc}", file=sys.stderr)
            return 2
    else:
        print(rendered_yaml, end="")

    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_templater_parser(subparsers)

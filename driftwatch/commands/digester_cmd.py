"""CLI sub-commands for config digest operations.

Sub-commands
------------
  driftwatch digest compute <env> <source> <live>
      Print the SHA-256 digest of both configs and whether they match.

  driftwatch digest save <env> <config>
      Compute and persist a digest for later comparison.

  driftwatch digest compare <env> <config>
      Compare a live config against the saved digest for *env*.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from driftwatch.digester import (
    DigesterError,
    compute_digest,
    digests_match,
    save_digest,
    load_digest,
)
from driftwatch.loader import ConfigLoadError, load_yaml

_DEFAULT_STORE = Path(".driftwatch") / "digests"


def _add_digester_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("digest", help="Compute and compare config digests")
    ss = p.add_subparsers(dest="digest_cmd", required=True)

    cmp = ss.add_parser("compute", help="Print digests for two configs")
    cmp.add_argument("env")
    cmp.add_argument("source", help="Source-of-truth YAML")
    cmp.add_argument("live", help="Live / deployed YAML")

    sv = ss.add_parser("save", help="Persist a digest for an env")
    sv.add_argument("env")
    sv.add_argument("config", help="YAML config to digest")
    sv.add_argument("--store", default=str(_DEFAULT_STORE))

    chk = ss.add_parser("compare", help="Compare live config against saved digest")
    chk.add_argument("env")
    chk.add_argument("config", help="Current YAML config")
    chk.add_argument("--store", default=str(_DEFAULT_STORE))

    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    if ns.digest_cmd == "compute":
        return _cmd_compute(ns)
    if ns.digest_cmd == "save":
        return _cmd_save(ns)
    if ns.digest_cmd == "compare":
        return _cmd_compare(ns)
    return 1


def _cmd_compute(ns: argparse.Namespace) -> int:
    try:
        src_cfg = load_yaml(ns.source)
        live_cfg = load_yaml(ns.live)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    src_d = compute_digest(ns.env, src_cfg)
    live_d = compute_digest(ns.env, live_cfg)
    print(f"source : {src_d.hexdigest}  ({src_d.key_count} keys)")
    print(f"live   : {live_d.hexdigest}  ({live_d.key_count} keys)")
    if digests_match(src_d, live_d):
        print("status : MATCH")
        return 0
    print("status : MISMATCH")
    return 1


def _cmd_save(ns: argparse.Namespace) -> int:
    try:
        cfg = load_yaml(ns.config)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    digest = compute_digest(ns.env, cfg)
    path = save_digest(digest, Path(ns.store))
    print(f"saved digest for '{ns.env}': {digest.hexdigest}")
    print(f"file : {path}")
    return 0


def _cmd_compare(ns: argparse.Namespace) -> int:
    try:
        cfg = load_yaml(ns.config)
        saved = load_digest(ns.env, Path(ns.store))
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except DigesterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    current = compute_digest(ns.env, cfg)
    print(f"saved  : {saved.hexdigest}")
    print(f"current: {current.hexdigest}")
    if digests_match(saved, current):
        print("status : MATCH – no drift detected")
        return 0
    print("status : MISMATCH – config has changed since last save")
    return 1


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_digester_parser(sub)

"""CLI sub-commands for environment profiling."""
from __future__ import annotations

import argparse
import json
import sys

from driftwatch.profiler import ProfilerError, capture_profile, diff_profiles, load_profile, save_profile


def _add_profiler_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("profile", help="Manage environment profiles")
    sub = p.add_subparsers(dest="profile_cmd", required=True)

    cap = sub.add_parser("capture", help="Capture and save a profile for ENV")
    cap.add_argument("env", help="Environment name")

    dif = sub.add_parser("diff", help="Diff two saved profiles")
    dif.add_argument("env_a", help="First environment")
    dif.add_argument("env_b", help="Second environment")

    sub.add_parser("list", help="List saved profiles (not yet implemented)")


def _cmd_capture(ns: argparse.Namespace) -> int:
    profile = capture_profile(ns.env)
    path = save_profile(profile)
    print(f"Profile saved: {path}")
    return 0


def _cmd_diff(ns: argparse.Namespace) -> int:
    try:
        a = load_profile(ns.env_a)
        b = load_profile(ns.env_b)
    except ProfilerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    changes = diff_profiles(a, b)
    if not changes:
        print(f"No differences between '{ns.env_a}' and '{ns.env_b}'.")
        return 0
    print(f"Differences between '{ns.env_a}' and '{ns.env_b}':")
    print(json.dumps(changes, indent=2))
    return 1


def _dispatch(ns: argparse.Namespace) -> int:
    if ns.profile_cmd == "capture":
        return _cmd_capture(ns)
    if ns.profile_cmd == "diff":
        return _cmd_diff(ns)
    print("Subcommand not implemented.", file=sys.stderr)
    return 2


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_profiler_parser(subparsers)

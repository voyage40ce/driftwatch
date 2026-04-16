"""CLI sub-commands for tag management."""
from __future__ import annotations

import argparse
from pathlib import Path

from driftwatch.tagging import TagError, delete_tag, get_tags, list_envs, set_tag

_DEFAULT_STORE = Path(".driftwatch/tags")


def _add_tagging_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("tag", help="Manage environment tags")
    sp = p.add_subparsers(dest="tag_cmd", required=True)

    # set
    s = sp.add_parser("set", help="Set a tag on an environment")
    s.add_argument("env")
    s.add_argument("key")
    s.add_argument("value")

    # get
    g = sp.add_parser("get", help="Show tags for an environment")
    g.add_argument("env")

    # delete
    d = sp.add_parser("delete", help="Delete a tag from an environment")
    d.add_argument("env")
    d.add_argument("key")

    # list
    sp.add_parser("list", help="List all tagged environments")

    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    store_dir = Path(getattr(ns, "store_dir", _DEFAULT_STORE))
    try:
        if ns.tag_cmd == "set":
            set_tag(store_dir, ns.env, ns.key, ns.value)
            print(f"Tagged {ns.env}: {ns.key}={ns.value}")
            return 0
        if ns.tag_cmd == "get":
            tags = get_tags(store_dir, ns.env)
            if not tags:
                print(f"No tags for {ns.env}")
            for k, v in sorted(tags.items()):
                print(f"  {k}={v}")
            return 0
        if ns.tag_cmd == "delete":
            removed = delete_tag(store_dir, ns.env, ns.key)
            if removed:
                print(f"Deleted tag {ns.key} from {ns.env}")
            else:
                print(f"Tag {ns.key} not found on {ns.env}")
            return 0
        if ns.tag_cmd == "list":
            envs = list_envs(store_dir)
            if not envs:
                print("No tagged environments.")
            for env in envs:
                print(f"  {env}")
            return 0
    except TagError as exc:
        print(f"tag error: {exc}")
        return 2
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    _add_tagging_parser(subparsers)

"""CLI sub-commands for environment tagging."""

from __future__ import annotations

import argparse

from driftwatch.tagging import TagError, delete_tag, get_tag, list_tags, set_tag


def _add_tagging_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("tag", help="Manage environment tags")
    sub = p.add_subparsers(dest="tag_cmd", required=True)

    # set
    s = sub.add_parser("set", help="Set a tag on an environment")
    s.add_argument("env", help="Environment name")
    s.add_argument("key", help="Tag key")
    s.add_argument("value", help="Tag value")

    # get
    g = sub.add_parser("get", help="Get a tag value for an environment")
    g.add_argument("env", help="Environment name")
    g.add_argument("key", help="Tag key")

    # list
    ls = sub.add_parser("list", help="List all tags for an environment")
    ls.add_argument("env", help="Environment name")

    # delete
    d = sub.add_parser("delete", help="Delete a tag from an environment")
    d.add_argument("env", help="Environment name")
    d.add_argument("key", help="Tag key")

    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        if ns.tag_cmd == "set":
            set_tag(ns.env, ns.key, ns.value)
            print(f"Tag '{ns.key}' set to '{ns.value}' for environment '{ns.env}'.")
            return 0

        if ns.tag_cmd == "get":
            value = get_tag(ns.env, ns.key)
            if value is None:
                print(f"Tag '{ns.key}' not found for environment '{ns.env}'.")
                return 1
            print(f"{ns.key}={value}")
            return 0

        if ns.tag_cmd == "list":
            tags = list_tags(ns.env)
            if not tags:
                print(f"No tags found for environment '{ns.env}'.")
                return 0
            for k, v in sorted(tags.items()):
                print(f"  {k}={v}")
            return 0

        if ns.tag_cmd == "delete":
            deleted = delete_tag(ns.env, ns.key)
            if deleted:
                print(f"Tag '{ns.key}' deleted from environment '{ns.env}'.")
                return 0
            print(f"Tag '{ns.key}' not found for environment '{ns.env}'.")
            return 1

    except TagError as exc:
        print(f"[tag error] {exc}")
        return 2

    return 0  # pragma: no cover


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the tag command group with the root parser."""
    _add_tagging_parser(subparsers)

"""CLI sub-command: driftwatch stream – stream drift reports as NDJSON."""
from __future__ import annotations

import argparse
import sys

from driftwatch.loader import ConfigLoadError, load_pair
from driftwatch.differ import diff
from driftwatch.streamer import StreamOptions, StreamerError, stream_reports, stream_to_file


def _add_streamer_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("stream", help="Stream drift reports as NDJSON")
    p.add_argument("source", help="Source (truth) YAML file")
    p.add_argument("deployed", help="Deployed YAML file")
    p.add_argument("--env", default="default", help="Environment label (default: 'default')")
    p.add_argument("--output", "-o", default=None, help="Write NDJSON to this file (default: stdout)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print each JSON record")
    p.add_argument("--skip-clean", action="store_true", help="Omit reports with no drift")
    p.set_defaults(func=_dispatch)


def _dispatch(ns: argparse.Namespace) -> int:
    try:
        source, deployed = load_pair(ns.source, ns.deployed)
    except ConfigLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = diff(source, deployed, env=ns.env)
    options = StreamOptions(
        pretty=ns.pretty,
        include_clean=not ns.skip_clean,
    )

    try:
        if ns.output:
            count = stream_to_file([report], ns.output, options=options)
            print(f"Wrote {count} record(s) to {ns.output}")
        else:
            list(stream_reports([report], options=options, out=sys.stdout))
    except StreamerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 1 if report.has_drift else 0


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _add_streamer_parser(subparsers)

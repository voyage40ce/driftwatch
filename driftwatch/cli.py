"""Entry point for the driftwatch CLI tool."""

import sys
import argparse

from driftwatch.loader import load_pair, ConfigLoadError
from driftwatch.differ import diff
from driftwatch.reporter import ReportOptions, print_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driftwatch",
        description="Detect configuration drift between deployed environments and source-of-truth YAML files.",
    )
    parser.add_argument(
        "expected",
        metavar="EXPECTED",
        help="Path to the source-of-truth YAML file.",
    )
    parser.add_argument(
        "actual",
        metavar="ACTUAL",
        help="Path to the deployed/actual YAML file.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored terminal output.",
    )
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Include unchanged keys in the report.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        expected_cfg, actual_cfg = load_pair(args.expected, args.actual)
    except ConfigLoadError as exc:
        print(f"Error loading configuration: {exc}", file=sys.stderr)
        return 2

    report = diff(expected_cfg, actual_cfg)

    options = ReportOptions(
        use_color=not args.no_color,
        show_unchanged=args.show_unchanged,
    )
    print_report(report, options)

    return 1 if report.diffs else 0


if __name__ == "__main__":
    sys.exit(main())

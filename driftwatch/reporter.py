"""Formats and outputs DriftReport results to the terminal."""

from dataclasses import dataclass
from typing import Optional
from driftwatch.differ import DriftReport

TERMINAL_WIDTH = 72

COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


@dataclass
class ReportOptions:
    use_color: bool = True
    show_unchanged: bool = False
    output_format: str = "text"  # "text" or "summary"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{COLOR_RESET}"


def _format_change(key: str, change: dict, use_color: bool) -> str:
    kind = change["type"]
    if kind == "changed":
        old = change["expected"]
        new = change["actual"]
        label = _colorize("CHANGED", COLOR_YELLOW, use_color)
        return f"  [{label}] {key}: {old!r} -> {new!r}"
    elif kind == "added":
        label = _colorize("ADDED", COLOR_GREEN, use_color)
        return f"  [{label}]  {key}: {change['actual']!r}"
    elif kind == "removed":
        label = _colorize("REMOVED", COLOR_RED, use_color)
        return f"  [{label}] {key}: {change['expected']!r}"
    return f"  [UNKNOWN] {key}"


def format_report(report: DriftReport, options: Optional[ReportOptions] = None) -> str:
    if options is None:
        options = ReportOptions()

    lines = []
    header = _colorize("DriftWatch Report", COLOR_BOLD, options.use_color)
    lines.append(header)
    lines.append("-" * TERMINAL_WIDTH)

    if not report.diffs:
        lines.append(_colorize("  No drift detected. Configurations match.", COLOR_GREEN, options.use_color))
    else:
        lines.append(f"  Drift detected — {len(report.diffs)} difference(s) found:")
        lines.append("")
        for key, change in sorted(report.diffs.items()):
            lines.append(_format_change(key, change, options.use_color))

    lines.append("-" * TERMINAL_WIDTH)
    status = "DRIFT" if report.diffs else "OK"
    color = COLOR_RED if report.diffs else COLOR_GREEN
    lines.append(f"  Status: {_colorize(status, color, options.use_color)}")
    return "\n".join(lines)


def print_report(report: DriftReport, options: Optional[ReportOptions] = None) -> None:
    print(format_report(report, options))

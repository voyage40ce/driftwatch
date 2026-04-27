"""highlighter.py – mark drift report items that match key patterns as highlighted.

Highlighting is purely additive: the original DriftReport is not mutated;
a new HighlightResult is returned that carries both the original items and
the subset that matched at least one pattern.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from driftwatch.differ import DriftReport


class HighlighterError(Exception):
    """Raised when highlighter configuration is invalid."""


@dataclass
class HighlightOptions:
    patterns: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    placeholder: str = "*** HIGHLIGHTED ***"


@dataclass
class HighlightResult:
    env: str
    all_items: List[dict]
    highlighted: List[dict]

    @property
    def highlight_count(self) -> int:
        return len(self.highlighted)

    @property
    def has_highlights(self) -> bool:
        return bool(self.highlighted)


def _compile_patterns(patterns: Sequence[str], case_sensitive: bool) -> List[re.Pattern]:
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, flags))
        except re.error as exc:
            raise HighlighterError(f"Invalid pattern {p!r}: {exc}") from exc
    return compiled


def _matches(key: str, compiled: List[re.Pattern]) -> bool:
    return any(rx.search(key) for rx in compiled)


def highlight_report(
    report: DriftReport,
    options: Optional[HighlightOptions] = None,
) -> HighlightResult:
    """Return a HighlightResult marking items whose keys match *options.patterns*."""
    if not isinstance(report, DriftReport):
        raise HighlighterError("highlight_report requires a DriftReport instance")

    opts = options or HighlightOptions()
    compiled = _compile_patterns(opts.patterns, opts.case_sensitive)

    all_items = list(report.changes)
    highlighted: List[dict] = []

    if compiled:
        for item in all_items:
            key = item.get("key", "")
            if _matches(key, compiled):
                highlighted.append(item)

    return HighlightResult(
        env=report.env,
        all_items=all_items,
        highlighted=highlighted,
    )


def format_highlight_summary(result: HighlightResult) -> str:
    lines = [
        f"Environment : {result.env}",
        f"Total items : {len(result.all_items)}",
        f"Highlighted : {result.highlight_count}",
    ]
    if result.has_highlights:
        lines.append("Keys:")
        for item in result.highlighted:
            lines.append(f"  - {item.get('key')}  [{item.get('change_type', '?')}]")
    return "\n".join(lines)

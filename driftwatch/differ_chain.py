"""differ_chain.py — Chain multiple DriftReports into a sequential diff pipeline.

Allows users to compare configs across a series of snapshots or environments,
producing a list of DriftReports that represent each step in the chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from driftwatch.differ import DriftReport, diff


class DiffChainError(Exception):
    """Raised when the diff chain cannot be constructed or executed."""


@dataclass
class ChainLink:
    """A single step in the diff chain.

    Attributes:
        label:  Human-readable name for this step (e.g. "dev→staging").
        report: The DriftReport produced by comparing the two configs.
    """

    label: str
    report: DriftReport


@dataclass
class ChainResult:
    """The result of running a full diff chain.

    Attributes:
        links:        Ordered list of ChainLinks, one per adjacent pair.
        total_drift:  Total number of drift items across all links.
    """

    links: List[ChainLink] = field(default_factory=list)

    @property
    def total_drift(self) -> int:
        """Sum of drift items across every link in the chain."""
        return sum(len(lnk.report.changes) for lnk in self.links)

    @property
    def has_drift(self) -> bool:
        """True if any link in the chain has drift."""
        return self.total_drift > 0


def build_chain(
    configs: List[Dict[str, Any]],
    labels: Optional[List[str]] = None,
) -> ChainResult:
    """Compare a sequence of configs pairwise and return a ChainResult.

    Each adjacent pair ``(configs[i], configs[i+1])`` is diffed; the result
    is stored as a :class:`ChainLink`.  If *labels* is provided it must have
    the same length as *configs*; the link label is then
    ``"<labels[i]>→<labels[i+1]>"``.  Otherwise numeric indices are used.

    Args:
        configs: Ordered list of configuration dicts (at least 2 required).
        labels:  Optional human-readable name for each config in the chain.

    Returns:
        A :class:`ChainResult` containing one link per adjacent pair.

    Raises:
        DiffChainError: If fewer than two configs are supplied, or if the
                        length of *labels* does not match *configs*.
    """
    if len(configs) < 2:
        raise DiffChainError(
            f"build_chain requires at least 2 configs, got {len(configs)}."
        )

    if labels is not None and len(labels) != len(configs):
        raise DiffChainError(
            f"labels length ({len(labels)}) must match configs length ({len(configs)})."
        )

    result = ChainResult()

    for i in range(len(configs) - 1):
        left = configs[i]
        right = configs[i + 1]

        if labels is not None:
            label = f"{labels[i]}\u2192{labels[i + 1]}"
        else:
            label = f"{i}\u2192{i + 1}"

        report = diff(left, right)
        result.links.append(ChainLink(label=label, report=report))

    return result


def format_chain_summary(
    result: ChainResult,
    *,
    color: bool = False,
) -> str:
    """Return a human-readable summary of a :class:`ChainResult`.

    Args:
        result: The chain result to format.
        color:  If *True*, ANSI colour codes are added (red for drift,
                green for clean).

    Returns:
        A multi-line string summarising each link.
    """
    _RED = "\033[31m" if color else ""
    _GREEN = "\033[32m" if color else ""
    _RESET = "\033[0m" if color else ""

    lines: List[str] = [
        f"Diff chain — {len(result.links)} step(s), "
        f"{result.total_drift} total drift item(s)",
        "-" * 48,
    ]

    for lnk in result.links:
        count = len(lnk.report.changes)
        if count:
            status = f"{_RED}{count} drift item(s){_RESET}"
        else:
            status = f"{_GREEN}clean{_RESET}"
        lines.append(f"  {lnk.label:<30}  {status}")

    return "\n".join(lines)

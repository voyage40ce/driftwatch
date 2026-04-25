"""sampler.py – randomly sample a subset of drift report items for spot-checking."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport


class SamplerError(Exception):
    """Raised when sampling cannot be performed."""


@dataclass
class SampleResult:
    env: str
    total_items: int
    sampled_items: list = field(default_factory=list)
    seed: Optional[int] = None

    @property
    def sample_count(self) -> int:
        return len(self.sampled_items)


def sample_report(
    report: DriftReport,
    n: int,
    *,
    seed: Optional[int] = None,
) -> SampleResult:
    """Return a SampleResult containing up to *n* randomly chosen drift items.

    Args:
        report: The DriftReport to sample from.
        n:      Maximum number of items to return.  Must be >= 1.
        seed:   Optional RNG seed for reproducibility.

    Raises:
        SamplerError: If *report* is not a DriftReport or *n* is invalid.
    """
    if not isinstance(report, DriftReport):
        raise SamplerError("report must be a DriftReport instance")
    if n < 1:
        raise SamplerError("n must be >= 1")

    items = list(report.changes)
    rng = random.Random(seed)
    sampled = rng.sample(items, min(n, len(items)))

    return SampleResult(
        env=report.env,
        total_items=len(items),
        sampled_items=sampled,
        seed=seed,
    )


def format_sample_summary(result: SampleResult) -> str:
    """Return a human-readable summary of a SampleResult."""
    lines: List[str] = [
        f"Environment : {result.env}",
        f"Total items : {result.total_items}",
        f"Sampled     : {result.sample_count}",
    ]
    if result.seed is not None:
        lines.append(f"Seed        : {result.seed}")
    if result.sampled_items:
        lines.append("Items:")
        for item in result.sampled_items:
            lines.append(f"  [{item.change_type}] {item.key}")
    else:
        lines.append("  (no drift items to sample)")
    return "\n".join(lines)

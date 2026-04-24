"""splitter.py – split a DriftReport into per-environment sub-reports.

Useful when a single diff run covers multiple logical environments and
you want to route each environment's changes separately (e.g. to
different audit logs or notification channels).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from driftwatch.differ import DriftReport


class SplitterError(Exception):
    """Raised when splitting fails due to bad input."""


@dataclass
class SplitResult:
    """Holds per-environment DriftReports produced by :func:`split_report`."""

    reports: Dict[str, DriftReport] = field(default_factory=dict)

    def environments(self) -> List[str]:
        """Return sorted list of environment names present in the split."""
        return sorted(self.reports.keys())

    def get(self, env: str) -> DriftReport:
        """Return the DriftReport for *env*, raising KeyError if absent."""
        if env not in self.reports:
            raise KeyError(f"No report found for environment '{env}'")
        return self.reports[env]


def split_report(report: DriftReport, env_prefix_sep: str = ".") -> SplitResult:
    """Split *report* by the first segment of each key path.

    Keys that contain *env_prefix_sep* are assumed to be prefixed with an
    environment name, e.g. ``"production.database.host"``.
    Keys without the separator are collected under the special bucket
    ``"__global__"``.

    Parameters
    ----------
    report:
        The :class:`~driftwatch.differ.DriftReport` to split.
    env_prefix_sep:
        Separator character used to identify the environment prefix.
        Defaults to ``"."``.

    Returns
    -------
    SplitResult
        A :class:`SplitResult` whose ``reports`` dict maps each detected
        environment name to a new :class:`DriftReport`.
    """
    if not isinstance(report, DriftReport):
        raise SplitterError("report must be a DriftReport instance")

    buckets: Dict[str, list] = {}

    for change in report.changes:
        if env_prefix_sep in change.key:
            env, _, rest = change.key.partition(env_prefix_sep)
        else:
            env = "__global__"
            rest = change.key

        buckets.setdefault(env, [])

        # Build a shallow copy of the change with the env prefix stripped.
        stripped = change.__class__(
            key=rest,
            source_value=change.source_value,
            deployed_value=change.deployed_value,
            change_type=change.change_type,
        )
        buckets[env].append(stripped)

    result = SplitResult()
    for env, changes in buckets.items():
        result.reports[env] = DriftReport(changes=changes)

    return result


def format_split_summary(result: SplitResult) -> str:
    """Return a human-readable summary of a :class:`SplitResult`."""
    if not result.reports:
        return "No environments found in split result."

    lines = [f"Split result – {len(result.reports)} environment(s):"]
    for env in result.environments():
        rpt = result.reports[env]
        lines.append(f"  {env}: {len(rpt.changes)} change(s)")
    return "\n".join(lines)

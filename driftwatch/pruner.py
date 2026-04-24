"""pruner.py – remove drift report items that match a set of suppression rules.

A suppression rule is a mapping with:
  - key_pattern  : glob-style pattern matched against the flattened key
  - change_types : optional list of change types to suppress (changed/added/removed)
                   if omitted, all change types for matching keys are suppressed
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.differ import DriftReport


class PrunerError(Exception):
    """Raised when pruner configuration is invalid."""


@dataclass
class PruneRule:
    key_pattern: str
    change_types: Optional[List[str]] = None  # None means all types


@dataclass
class PruneResult:
    kept: List[dict] = field(default_factory=list)
    pruned: List[dict] = field(default_factory=list)

    @property
    def pruned_count(self) -> int:
        return len(self.pruned)

    @property
    def kept_count(self) -> int:
        return len(self.kept)


def _matches_rule(item: dict, rule: PruneRule) -> bool:
    key = item.get("key", "")
    if not fnmatch.fnmatch(key, rule.key_pattern):
        return False
    if rule.change_types is None:
        return True
    return item.get("change_type") in rule.change_types


def load_prune_rules(raw: list) -> List[PruneRule]:
    """Parse a list of raw dicts into PruneRule objects."""
    if not isinstance(raw, list):
        raise PrunerError("prune rules must be a list")
    rules: List[PruneRule] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise PrunerError(f"rule at index {idx} must be a mapping")
        if "key_pattern" not in entry:
            raise PrunerError(f"rule at index {idx} missing 'key_pattern'")
        change_types = entry.get("change_types")
        if change_types is not None and not isinstance(change_types, list):
            raise PrunerError(f"rule at index {idx}: 'change_types' must be a list")
        rules.append(PruneRule(key_pattern=entry["key_pattern"], change_types=change_types))
    return rules


def prune_report(report: DriftReport, rules: List[PruneRule]) -> PruneResult:
    """Apply suppression rules to a DriftReport, returning a PruneResult."""
    if not isinstance(report, DriftReport):
        raise PrunerError("report must be a DriftReport instance")
    result = PruneResult()
    for item in report.changes:
        suppressed = any(_matches_rule(item, rule) for rule in rules)
        if suppressed:
            result.pruned.append(item)
        else:
            result.kept.append(item)
    return result


def format_prune_summary(result: PruneResult) -> str:
    lines = [
        f"Pruned : {result.pruned_count} item(s)",
        f"Kept   : {result.kept_count} item(s)",
    ]
    if result.pruned:
        lines.append("Suppressed keys:")
        for item in result.pruned:
            lines.append(f"  - [{item.get('change_type', '?')}] {item.get('key', '?')}")
    return "\n".join(lines)

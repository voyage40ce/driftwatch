"""merger.py – merge two config dicts with conflict tracking."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


class MergerError(Exception):
    """Raised when merging fails."""


@dataclass
class MergeResult:
    merged: dict[str, Any]
    conflicts: list[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def _merge(base: dict, override: dict, prefix: str = "") -> MergeResult:
    merged: dict[str, Any] = {}
    conflicts: list[str] = []

    all_keys = set(base) | set(override)
    for key in all_keys:
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if key in base and key in override:
            bv, ov = base[key], override[key]
            if isinstance(bv, dict) and isinstance(ov, dict):
                sub = _merge(bv, ov, prefix=full_key)
                merged[key] = sub.merged
                conflicts.extend(sub.conflicts)
            elif bv != ov:
                conflicts.append(full_key)
                merged[key] = ov
            else:
                merged[key] = bv
        elif key in base:
            merged[key] = base[key]
        else:
            merged[key] = override[key]

    return MergeResult(merged=merged, conflicts=conflicts)


def merge_configs(base: dict, override: dict) -> MergeResult:
    """Merge *override* into *base*, returning a MergeResult.

    Nested dicts are merged recursively.  Keys present in both with
    differing scalar values are recorded as conflicts; the override
    value wins.
    """
    if not isinstance(base, dict) or not isinstance(override, dict):
        raise MergerError("Both base and override must be dicts")
    return _merge(base, override)


def format_merge_summary(result: MergeResult) -> str:
    lines = []
    if result.has_conflicts:
        lines.append(f"Conflicts ({len(result.conflicts)}):")
        for c in result.conflicts:
            lines.append(f"  ! {c}")
    else:
        lines.append("No conflicts – merge clean.")
    return "\n".join(lines)

"""Compare two environment profiles and produce a structured comparison report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from driftwatch.profiler import EnvProfile
from driftwatch.differ import _flatten


class ComparatorError(Exception):
    """Raised when profile comparison fails."""


@dataclass
class ProfileDiff:
    env_a: str
    env_b: str
    added: dict[str, Any] = field(default_factory=dict)    # in b, not in a
    removed: dict[str, Any] = field(default_factory=dict)  # in a, not in b
    changed: dict[str, tuple[Any, Any]] = field(default_factory=dict)  # key: (a_val, b_val)

    @property
    def has_diff(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def compare_profiles(a: EnvProfile, b: EnvProfile) -> ProfileDiff:
    """Return a ProfileDiff between two EnvProfile objects."""
    flat_a = _flatten(a.config)
    flat_b = _flatten(b.config)

    keys_a = set(flat_a)
    keys_b = set(flat_b)

    added = {k: flat_b[k] for k in keys_b - keys_a}
    removed = {k: flat_a[k] for k in keys_a - keys_b}
    changed = {
        k: (flat_a[k], flat_b[k])
        for k in keys_a & keys_b
        if flat_a[k] != flat_b[k]
    }

    return ProfileDiff(
        env_a=a.env,
        env_b=b.env,
        added=added,
        removed=removed,
        changed=changed,
    )


def format_profile_diff(diff: ProfileDiff) -> str:
    """Return a human-readable string for a ProfileDiff."""
    lines: list[str] = []
    lines.append(f"Comparing '{diff.env_a}' vs '{diff.env_b}'")
    if not diff.has_diff:
        lines.append("  No differences found.")
        return "\n".join(lines)

    for k, v in sorted(diff.added.items()):
        lines.append(f"  + {k}: {v}")
    for k, v in sorted(diff.removed.items()):
        lines.append(f"  - {k}: {v}")
    for k, (va, vb) in sorted(diff.changed.items()):
        lines.append(f"  ~ {k}: {va!r} -> {vb!r}")
    return "\n".join(lines)

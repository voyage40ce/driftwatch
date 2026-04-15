"""Flat-key diff engine for driftwatch.

Compares two configuration dictionaries and reports added, removed, and
changed keys using dot-notation paths (e.g. ``database.host``).
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DriftReport:
    """Result of comparing a source-of-truth config against a deployed config."""

    added: dict[str, Any] = field(default_factory=dict)
    """Keys present in *deployed* but missing from source-of-truth."""

    removed: dict[str, Any] = field(default_factory=dict)
    """Keys present in *source-of-truth* but missing from deployed."""

    changed: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    """Keys whose values differ: mapping of key -> (expected, actual)."""

    @property
    def has_drift(self) -> bool:
        """Return True when any difference was detected."""
        return bool(self.added or self.removed or self.changed)


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Recursively flatten a nested dict to dot-notation keys."""
    items: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            items.update(_flatten(value, full_key))
    else:
        items[prefix] = obj
    return items


def diff(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> DriftReport:
    """Compare *expected* (source-of-truth) against *actual* (deployed).

    Args:
        expected: Canonical configuration dictionary.
        actual:   Deployed configuration dictionary.

    Returns:
        A :class:`DriftReport` describing the differences.
    """
    flat_expected = _flatten(expected)
    flat_actual = _flatten(actual)

    all_keys = set(flat_expected) | set(flat_actual)
    report = DriftReport()

    for key in sorted(all_keys):
        in_expected = key in flat_expected
        in_actual = key in flat_actual

        if in_expected and not in_actual:
            report.removed[key] = flat_expected[key]
        elif in_actual and not in_expected:
            report.added[key] = flat_actual[key]
        elif flat_expected[key] != flat_actual[key]:
            report.changed[key] = (flat_expected[key], flat_actual[key])

    return report

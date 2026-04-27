"""flattener.py – flatten a nested config dict into dot-notation key/value pairs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class FlattenerError(Exception):
    """Raised when flattening fails."""


@dataclass
class FlatEntry:
    key: str
    value: Any
    depth: int


@dataclass
class FlatResult:
    env: str
    entries: List[FlatEntry] = field(default_factory=list)

    @property
    def key_count(self) -> int:
        return len(self.entries)

    def as_dict(self) -> Dict[str, Any]:
        return {e.key: e.value for e in self.entries}


def _flatten_dict(
    obj: Any,
    prefix: str = "",
    depth: int = 0,
    sep: str = ".",
) -> List[FlatEntry]:
    """Recursively flatten *obj* into a list of FlatEntry items."""
    if not isinstance(obj, dict):
        raise FlattenerError(
            f"Expected a dict at '{prefix or 'root'}', got {type(obj).__name__}"
        )

    entries: List[FlatEntry] = []
    for k, v in obj.items():
        full_key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            entries.extend(_flatten_dict(v, prefix=full_key, depth=depth + 1, sep=sep))
        else:
            entries.append(FlatEntry(key=full_key, value=v, depth=depth))
    return entries


def flatten_config(
    config: Dict[str, Any],
    env: str = "unknown",
    sep: str = ".",
) -> FlatResult:
    """Flatten *config* and return a :class:`FlatResult`.

    Args:
        config: Nested configuration dictionary.
        env:    Logical environment name attached to the result.
        sep:    Key separator (default ``'.'``).

    Returns:
        A :class:`FlatResult` containing one :class:`FlatEntry` per leaf.

    Raises:
        :class:`FlattenerError` if *config* is not a dict.
    """
    if not isinstance(config, dict):
        raise FlattenerError(f"config must be a dict, got {type(config).__name__}")
    entries = _flatten_dict(config, sep=sep)
    return FlatResult(env=env, entries=entries)


def format_flat_summary(result: FlatResult) -> str:
    """Return a human-readable summary of *result*."""
    lines = [f"Flattened config for '{result.env}' ({result.key_count} keys):"]
    for entry in sorted(result.entries, key=lambda e: e.key):
        lines.append(f"  {entry.key} = {entry.value!r}  (depth {entry.depth})")
    return "\n".join(lines)

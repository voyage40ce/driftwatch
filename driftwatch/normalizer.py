"""Normalize config values for consistent comparison."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class NormalizerError(Exception):
    """Raised when normalization fails."""


@dataclass
class NormalizeOptions:
    lowercase_keys: bool = True
    strip_string_values: bool = True
    coerce_booleans: bool = True
    remove_none_values: bool = False
    ignored_keys: list[str] = field(default_factory=list)


_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, str):
        if value.lower() in _BOOL_TRUE:
            return True
        if value.lower() in _BOOL_FALSE:
            return False
    return value


def _normalize_value(value: Any, opts: NormalizeOptions) -> Any:
    if isinstance(value, dict):
        return normalize_config(value, opts)
    if isinstance(value, list):
        return [_normalize_value(v, opts) for v in value]
    if isinstance(value, str):
        if opts.strip_string_values:
            value = value.strip()
        if opts.coerce_booleans:
            value = _coerce_bool(value)
        return value
    return value


def normalize_config(config: dict[str, Any], opts: NormalizeOptions | None = None) -> dict[str, Any]:
    """Return a new dict with normalized keys and values."""
    if not isinstance(config, dict):
        raise NormalizerError(f"Expected a dict, got {type(config).__name__}")
    if opts is None:
        opts = NormalizeOptions()

    result: dict[str, Any] = {}
    for key, value in config.items():
        normalized_key = key.lower() if opts.lowercase_keys else key
        if normalized_key in opts.ignored_keys:
            result[normalized_key] = value
            continue
        normalized_value = _normalize_value(value, opts)
        if opts.remove_none_values and normalized_value is None:
            continue
        result[normalized_key] = normalized_value
    return result

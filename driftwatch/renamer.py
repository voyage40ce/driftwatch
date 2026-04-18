"""renamer.py – rename keys in a config dict based on a mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


class RenamerError(Exception):
    """Raised when renaming fails."""


@dataclass
class RenameResult:
    config: Dict[str, Any]
    renamed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _rename_flat(config: Dict[str, Any], mapping: Dict[str, str]) -> RenameResult:
    """Apply a flat key->new_key mapping to a config dict (dot-notation keys)."""
    result: Dict[str, Any] = {}
    renamed: list[str] = []
    skipped: list[str] = []

    for k, v in config.items():
        if k in mapping:
            new_key = mapping[k]
            if new_key in config and new_key not in mapping:
                skipped.append(k)
                result[k] = v
            else:
                result[new_key] = v
                renamed.append(k)
        else:
            result[k] = v

    return RenameResult(config=result, renamed=renamed, skipped=skipped)


def _set_nested(d: Dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def _del_nested(d: Dict[str, Any], key: str) -> None:
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in d:
            return
        d = d[part]
    d.pop(parts[-1], None)


def _get_nested(d: Dict[str, Any], key: str) -> Any:
    parts = key.split(".")
    for part in parts:
        if not isinstance(d, dict) or part not in d:
            raise KeyError(key)
        d = d[part]
    return d


def rename_config(
    config: Dict[str, Any], mapping: Dict[str, str]
) -> RenameResult:
    """Rename dot-notation keys in a nested config dict."""
    if not isinstance(mapping, dict):
        raise RenamerError("mapping must be a dict")

    import copy
    out = copy.deepcopy(config)
    renamed: list[str] = []
    skipped: list[str] = []

    for old_key, new_key in mapping.items():
        try:
            value = _get_nested(out, old_key)
        except KeyError:
            skipped.append(old_key)
            continue
        try:
            _get_nested(out, new_key)
            # destination already exists – skip to avoid overwrite
            skipped.append(old_key)
            continue
        except KeyError:
            pass
        _del_nested(out, old_key)
        _set_nested(out, new_key, value)
        renamed.append(old_key)

    return RenameResult(config=out, renamed=renamed, skipped=skipped)

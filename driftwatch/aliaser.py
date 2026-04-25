"""aliaser.py – map canonical config keys to human-friendly aliases.

Allows users to define a YAML alias map so that internal dot-notation
keys like ``db.host`` are displayed (or exported) as ``Database Host``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from driftwatch.loader import ConfigLoadError


class AliasError(Exception):
    """Raised when alias operations fail."""


@dataclass
class AliasMap:
    """Holds the bidirectional mapping between keys and their aliases."""

    _forward: Dict[str, str] = field(default_factory=dict)   # key -> alias
    _reverse: Dict[str, str] = field(default_factory=dict)   # alias -> key

    def add(self, key: str, alias: str) -> None:
        self._forward[key] = alias
        self._reverse[alias] = key

    def alias_for(self, key: str) -> Optional[str]:
        return self._forward.get(key)

    def key_for(self, alias: str) -> Optional[str]:
        return self._reverse.get(alias)

    def all_aliases(self) -> Dict[str, str]:
        return dict(self._forward)


def load_alias_map(path: str) -> AliasMap:
    """Load an alias map from a YAML file.

    Expected format::

        aliases:
          db.host: Database Host
          app.port: Application Port
    """
    p = Path(path)
    if not p.exists():
        raise AliasError(f"Alias file not found: {path}")
    try:
        raw = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        raise AliasError(f"Invalid YAML in alias file: {exc}") from exc

    if not isinstance(raw, dict) or "aliases" not in raw:
        raise AliasError("Alias file must contain a top-level 'aliases' mapping.")

    mapping = raw["aliases"]
    if not isinstance(mapping, dict):
        raise AliasError("'aliases' must be a key-value mapping.")

    alias_map = AliasMap()
    for key, alias in mapping.items():
        alias_map.add(str(key), str(alias))
    return alias_map


def apply_aliases(data: Dict[str, str], alias_map: AliasMap) -> Dict[str, str]:
    """Return a copy of *data* with keys replaced by their aliases where defined."""
    return {
        alias_map.alias_for(k) or k: v
        for k, v in data.items()
    }


def resolve_aliases(data: Dict[str, str], alias_map: AliasMap) -> Dict[str, str]:
    """Return a copy of *data* with alias keys resolved back to canonical keys."""
    return {
        alias_map.key_for(k) or k: v
        for k, v in data.items()
    }

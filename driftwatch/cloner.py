"""cloner.py – deep-copy and remap a config under a new environment name."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from driftwatch.loader import load_yaml, ConfigLoadError


class ClonerError(Exception):
    """Raised when a clone operation fails."""


@dataclass
class CloneResult:
    source_env: str
    target_env: str
    config: Dict[str, Any]
    overrides_applied: int = 0
    skipped_keys: list = field(default_factory=list)


def clone_config(
    source: Dict[str, Any],
    source_env: str,
    target_env: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> CloneResult:
    """Deep-copy *source* and apply optional *overrides*, returning a CloneResult."""
    if not isinstance(source, dict):
        raise ClonerError("source config must be a mapping")
    if not target_env:
        raise ClonerError("target_env must not be empty")

    cloned: Dict[str, Any] = copy.deepcopy(source)
    applied = 0
    skipped: list = []

    for key, value in (overrides or {}).items():
        parts = key.split(".")
        node = cloned
        try:
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
            applied += 1
        except (TypeError, AttributeError):
            skipped.append(key)

    return CloneResult(
        source_env=source_env,
        target_env=target_env,
        config=cloned,
        overrides_applied=applied,
        skipped_keys=skipped,
    )


def clone_from_file(
    path: str,
    source_env: str,
    target_env: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> CloneResult:
    """Load a YAML file and clone it."""
    try:
        cfg = load_yaml(path)
    except ConfigLoadError as exc:
        raise ClonerError(str(exc)) from exc
    return clone_config(cfg, source_env, target_env, overrides)


def format_clone_summary(result: CloneResult) -> str:
    lines = [
        f"Cloned '{result.source_env}' → '{result.target_env}'",
        f"  Overrides applied : {result.overrides_applied}",
    ]
    if result.skipped_keys:
        lines.append(f"  Skipped keys      : {', '.join(result.skipped_keys)}")
    return "\n".join(lines)

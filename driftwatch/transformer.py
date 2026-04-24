"""transformer.py – apply a sequence of key-value transformations to a config dict."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class TransformerError(Exception):
    """Raised when a transformation cannot be applied."""


@dataclass
class TransformRule:
    """A single named transformation rule."""
    name: str
    pattern: str          # regex matched against flattened dot-notation key
    operation: str        # "set", "delete", "prefix", "suffix", "uppercase", "lowercase"
    value: Optional[str] = None  # used by "set", "prefix", "suffix"


@dataclass
class TransformResult:
    config: Dict[str, Any]
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)


def _get_nested(cfg: dict, parts: List[str]) -> Any:
    cur = cfg
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            raise KeyError(p)
        cur = cur[p]
    return cur


def _set_nested(cfg: dict, parts: List[str], value: Any) -> None:
    cur = cfg
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def _del_nested(cfg: dict, parts: List[str]) -> None:
    cur = cfg
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return
        cur = cur[p]
    cur.pop(parts[-1], None)


def _flatten_keys(cfg: dict, prefix: str = "") -> List[str]:
    keys: List[str] = []
    for k, v in cfg.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.extend(_flatten_keys(v, full))
        else:
            keys.append(full)
    return keys


_OPERATIONS: Dict[str, Callable[[Any, Optional[str]], Any]] = {
    "uppercase": lambda v, _: str(v).upper() if isinstance(v, str) else v,
    "lowercase": lambda v, _: str(v).lower() if isinstance(v, str) else v,
    "prefix":    lambda v, arg: f"{arg}{v}",
    "suffix":    lambda v, arg: f"{v}{arg}",
    "set":       lambda v, arg: arg,
}


def apply_transforms(config: Dict[str, Any], rules: List[TransformRule]) -> TransformResult:
    """Return a new config dict with all matching rules applied."""
    import copy
    result = copy.deepcopy(config)
    applied: List[str] = []
    skipped: List[str] = []

    for rule in rules:
        try:
            pat = re.compile(rule.pattern)
        except re.error as exc:
            raise TransformerError(f"Invalid pattern in rule '{rule.name}': {exc}") from exc

        matched_any = False
        for key in _flatten_keys(result):
            if not pat.search(key):
                continue
            parts = key.split(".")
            if rule.operation == "delete":
                _del_nested(result, parts)
                applied.append(f"{rule.name}:{key}")
                matched_any = True
            elif rule.operation in _OPERATIONS:
                try:
                    old_val = _get_nested(result, parts)
                except KeyError:
                    skipped.append(f"{rule.name}:{key}")
                    continue
                new_val = _OPERATIONS[rule.operation](old_val, rule.value)
                _set_nested(result, parts, new_val)
                applied.append(f"{rule.name}:{key}")
                matched_any = True
            else:
                raise TransformerError(f"Unknown operation '{rule.operation}' in rule '{rule.name}'")
        if not matched_any:
            skipped.append(rule.name)

    return TransformResult(config=result, applied=applied, skipped=skipped)

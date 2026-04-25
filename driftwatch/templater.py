"""Template rendering for config files using variable substitution."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from driftwatch.loader import ConfigLoadError


class TemplaterError(Exception):
    """Raised when template rendering fails."""


@dataclass
class RenderResult:
    rendered: dict[str, Any]
    substitutions: dict[str, str] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)

    @property
    def has_unresolved(self) -> bool:
        """Return True if any template variables could not be resolved."""
        return bool(self.unresolved)


_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def _substitute(value: str, variables: dict[str, str]) -> tuple[str, list[str], list[str]]:
    used: list[str] = []
    missing: list[str] = []

    def replacer(m: re.Match) -> str:
        key = m.group(1)
        if key in variables:
            used.append(key)
            return variables[key]
        missing.append(key)
        return m.group(0)

    result = _VAR_RE.sub(replacer, value)
    return result, used, missing


def _render_dict(
    obj: Any, variables: dict[str, str]
) -> tuple[Any, dict[str, str], list[str]]:
    subs: dict[str, str] = {}
    unresolved: list[str] = []
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            rv, s, u = _render_dict(v, variables)
            out[k] = rv
            subs.update(s)
            unresolved.extend(u)
        return out, subs, unresolved
    if isinstance(obj, list):
        out_list = []
        for item in obj:
            rv, s, u = _render_dict(item, variables)
            out_list.append(rv)
            subs.update(s)
            unresolved.extend(u)
        return out_list, subs, unresolved
    if isinstance(obj, str):
        rendered, used, missing = _substitute(obj, variables)
        for k in used:
            subs[k] = variables[k]
        unresolved.extend(missing)
        return rendered, subs, unresolved
    return obj, subs, unresolved


def render_template(template: dict[str, Any], variables: dict[str, str]) -> RenderResult:
    rendered, subs, unresolved = _render_dict(template, variables)
    return RenderResult(rendered=rendered, substitutions=subs, unresolved=list(set(unresolved)))


def load_template(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise TemplaterError(f"Template file not found: {path}")
    try:
        data = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        raise TemplaterError(f"Invalid YAML in template: {exc}") from exc
    if not isinstance(data, dict):
        raise TemplaterError("Template must be a YAML mapping")
    return data

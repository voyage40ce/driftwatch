"""inspector.py – Inspect a config dict and produce a structured field inventory."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class InspectorError(Exception):
    """Raised when inspection fails."""


@dataclass
class FieldInfo:
    key: str          # dot-notation path
    value_type: str   # python type name
    value: Any
    depth: int
    is_secret: bool = False


@dataclass
class InspectResult:
    env: str
    fields: List[FieldInfo] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.fields)

    @property
    def secret_count(self) -> int:
        return sum(1 for f in self.fields if f.is_secret)


_SECRET_RE = re.compile(
    r"(password|secret|token|key|credential|auth|api_?key)",
    re.IGNORECASE,
)


def _is_secret(key: str) -> bool:
    return bool(_SECRET_RE.search(key))


def _walk(
    obj: Any,
    prefix: str,
    depth: int,
    out: List[FieldInfo],
) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            _walk(v, full_key, depth + 1, out)
    else:
        out.append(
            FieldInfo(
                key=prefix,
                value_type=type(obj).__name__,
                value=obj,
                depth=depth,
                is_secret=_is_secret(prefix),
            )
        )


def inspect_config(config: Any, env: str = "unknown") -> InspectResult:
    """Walk *config* and return an :class:`InspectResult` with every leaf field."""
    if not isinstance(config, dict):
        raise InspectorError("inspect_config requires a mapping at the top level")
    result = InspectResult(env=env)
    _walk(config, "", 0, result.fields)
    return result


def format_inspect(result: InspectResult, show_values: bool = False) -> str:
    """Return a human-readable summary of an :class:`InspectResult`."""
    lines: List[str] = [
        f"Inspection report for env: {result.env}",
        f"  Total fields : {result.total}",
        f"  Secret fields: {result.secret_count}",
        "",
    ]
    for fi in result.fields:
        secret_marker = " [SECRET]" if fi.is_secret else ""
        value_part = f" = {fi.value!r}" if show_values and not fi.is_secret else ""
        lines.append(f"  {fi.key} ({fi.value_type}){secret_marker}{value_part}")
    return "\n".join(lines)

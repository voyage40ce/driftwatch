"""Redact sensitive keys from config dicts before display or export."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_DEFAULT_PATTERNS = [
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"private[_-]?key",
    r"credential",
]

REDACTED = "***REDACTED***"


class RedactorError(Exception):
    """Raised when redaction configuration is invalid."""


@dataclass
class RedactOptions:
    patterns: list[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    placeholder: str = REDACTED
    case_sensitive: bool = False


def _compile(patterns: list[str], case_sensitive: bool) -> list[re.Pattern]:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        return [re.compile(p, flags) for p in patterns]
    except re.error as exc:
        raise RedactorError(f"Invalid redaction pattern: {exc}") from exc


def redact_dict(
    data: dict[str, Any],
    opts: RedactOptions | None = None,
    _compiled: list[re.Pattern] | None = None,
) -> dict[str, Any]:
    """Return a copy of *data* with sensitive leaf values replaced."""
    if opts is None:
        opts = RedactOptions()
    if _compiled is None:
        _compiled = _compile(opts.patterns, opts.case_sensitive)

    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = redact_dict(value, opts, _compiled)
        elif any(p.search(str(key)) for p in _compiled):
            result[key] = opts.placeholder
        else:
            result[key] = value
    return result


def redact_flat(
    flat: dict[str, Any],
    opts: RedactOptions | None = None,
) -> dict[str, Any]:
    """Redact a flat (dot-notation) key/value mapping."""
    if opts is None:
        opts = RedactOptions()
    compiled = _compile(opts.patterns, opts.case_sensitive)
    return {
        k: (opts.placeholder if any(p.search(k) for p in compiled) else v)
        for k, v in flat.items()
    }

"""masker.py – selectively mask config values before display or export."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


class MaskerError(Exception):
    """Raised when masking configuration is invalid."""


@dataclass
class MaskOptions:
    """Controls which keys are masked and how."""
    patterns: list[str] = field(default_factory=lambda: [
        r"password", r"secret", r"token", r"api[_-]?key", r"private",
    ])
    placeholder: str = "***"
    case_sensitive: bool = False


@dataclass
class MaskResult:
    """Result of a masking operation."""
    config: dict[str, Any]
    masked_keys: list[str]

    @property
    def mask_count(self) -> int:
        return len(self.masked_keys)


def _compile_patterns(options: MaskOptions) -> list[re.Pattern]:
    flags = 0 if options.case_sensitive else re.IGNORECASE
    compiled = []
    for pat in options.patterns:
        try:
            compiled.append(re.compile(pat, flags))
        except re.error as exc:
            raise MaskerError(f"Invalid mask pattern {pat!r}: {exc}") from exc
    return compiled


def _is_sensitive(key: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(key) for p in patterns)


def _mask_dict(
    data: dict[str, Any],
    patterns: list[re.Pattern],
    placeholder: str,
    prefix: str = "",
) -> tuple[dict[str, Any], list[str]]:
    result: dict[str, Any] = {}
    masked: list[str] = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if _is_sensitive(key, patterns):
            result[key] = placeholder
            masked.append(full_key)
        elif isinstance(value, dict):
            nested, nested_masked = _mask_dict(value, patterns, placeholder, full_key)
            result[key] = nested
            masked.extend(nested_masked)
        else:
            result[key] = value
    return result, masked


def mask_config(
    config: dict[str, Any],
    options: MaskOptions | None = None,
) -> MaskResult:
    """Return a copy of *config* with sensitive values replaced by placeholder."""
    if not isinstance(config, dict):
        raise MaskerError("mask_config expects a dict")
    opts = options or MaskOptions()
    patterns = _compile_patterns(opts)
    masked_config, masked_keys = _mask_dict(config, patterns, opts.placeholder)
    return MaskResult(config=masked_config, masked_keys=masked_keys)


def format_mask_summary(result: MaskResult) -> str:
    """Return a human-readable summary of what was masked."""
    if result.mask_count == 0:
        return "No sensitive keys masked."
    lines = [f"Masked {result.mask_count} key(s):"]
    for key in sorted(result.masked_keys):
        lines.append(f"  - {key}")
    return "\n".join(lines)

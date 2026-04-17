"""patcher.py – apply a DriftReport as patches to a config dict."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from driftwatch.differ import DriftReport


class PatcherError(Exception):
    """Raised when patching fails."""


@dataclass
class PatchResult:
    patched: dict[str, Any]
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _set_nested(d: dict, key: str, value: Any) -> None:
    """Set a dot-notation key in a nested dict, creating intermediates."""
    parts = key.split(".")
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def _del_nested(d: dict, key: str) -> bool:
    """Delete a dot-notation key. Returns True if deleted."""
    parts = key.split(".")
    for part in parts[:-1]:
        if not isinstance(d, dict) or part not in d:
            return False
        d = d[part]
    if isinstance(d, dict) and parts[-1] in d:
        del d[parts[-1]]
        return True
    return False


def patch_config(
    config: dict[str, Any],
    report: DriftReport,
    *,
    skip_keys: list[str] | None = None,
    dry_run: bool = False,
) -> PatchResult:
    """Apply drift changes from *report* onto a copy of *config*.

    Added keys in the report are added; removed keys are deleted;
    changed keys take the expected (source-of-truth) value.
    """
    import copy

    skip = set(skip_keys or [])
    out = copy.deepcopy(config)
    applied: list[str] = []
    skipped: list[str] = []

    for item in report.changes:
        key = item["key"]
        if key in skip:
            skipped.append(key)
            continue
        kind = item["type"]
        if not dry_run:
            if kind in ("changed", "added"):
                _set_nested(out, key, item["expected"])
            elif kind == "removed":
                _del_nested(out, key)
        applied.append(key)

    return PatchResult(patched=out, applied=applied, skipped=skipped)


def format_patch_summary(result: PatchResult) -> str:
    lines = [f"Patch summary: {len(result.applied)} applied, {len(result.skipped)} skipped"]
    for k in result.applied:
        lines.append(f"  ~ {k}")
    for k in result.skipped:
        lines.append(f"  - {k} (skipped)")
    return "\n".join(lines)

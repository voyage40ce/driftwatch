"""throttler.py – rate-limit drift notifications so the same key does not
spam alerts within a configurable cooldown window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from driftwatch.differ import DriftReport


class ThrottlerError(Exception):
    """Raised when the throttler encounters a storage problem."""


@dataclass
class ThrottleOptions:
    cooldown_seconds: int = 300  # 5 minutes default
    store_dir: Path = Path(".driftwatch/throttle")


@dataclass
class ThrottleResult:
    env: str
    suppressed: List[str] = field(default_factory=list)
    passed: List[str] = field(default_factory=list)

    @property
    def suppressed_count(self) -> int:
        return len(self.suppressed)

    @property
    def passed_count(self) -> int:
        return len(self.passed)


def _state_path(store_dir: Path, env: str) -> Path:
    return store_dir / f"{env}.json"


def _load_state(path: Path) -> Dict[str, float]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ThrottlerError(f"Cannot read throttle state {path}: {exc}") from exc


def _save_state(path: Path, state: Dict[str, float]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2))
    except OSError as exc:
        raise ThrottlerError(f"Cannot write throttle state {path}: {exc}") from exc


def throttle_report(
    report: DriftReport,
    opts: ThrottleOptions | None = None,
) -> ThrottleResult:
    """Return a ThrottleResult indicating which changed keys pass the cooldown
    gate and which are suppressed.  The on-disk state is updated for every key
    that passes."""
    if opts is None:
        opts = ThrottleOptions()

    path = _state_path(opts.store_dir, report.env)
    state: Dict[str, float] = _load_state(path)
    now = time.time()
    result = ThrottleResult(env=report.env)

    for item in report.changes:
        last_seen = state.get(item.key, 0.0)
        if now - last_seen >= opts.cooldown_seconds:
            result.passed.append(item.key)
            state[item.key] = now
        else:
            result.suppressed.append(item.key)

    if result.passed:
        _save_state(path, state)

    return result


def format_throttle_summary(result: ThrottleResult) -> str:
    lines = [f"Throttle summary for '{result.env}':"]
    lines.append(f"  passed:     {result.passed_count}")
    lines.append(f"  suppressed: {result.suppressed_count}")
    if result.suppressed:
        for key in result.suppressed:
            lines.append(f"    - {key}")
    return "\n".join(lines)

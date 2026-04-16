"""Persist and retrieve diff results for historical comparison."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftReport

DEFAULT_DIR = Path.home() / ".driftwatch" / "diffstore"


class DiffStoreError(Exception):
    pass


@dataclass
class StoredDiff:
    env: str
    timestamp: float
    has_drift: bool
    changes: List[dict] = field(default_factory=list)


def _store_path(base_dir: Path, env: str) -> Path:
    return base_dir / f"{env}.jsonl"


def record_diff(report: DriftReport, env: str, base_dir: Path = DEFAULT_DIR) -> StoredDiff:
    base_dir.mkdir(parents=True, exist_ok=True)
    entry = StoredDiff(
        env=env,
        timestamp=time.time(),
        has_drift=report.has_drift,
        changes=[{"key": c.key, "source": c.source_value, "deployed": c.deployed_value} for c in report.changes],
    )
    path = _store_path(base_dir, env)
    with path.open("a") as f:
        f.write(json.dumps({
            "env": entry.env,
            "timestamp": entry.timestamp,
            "has_drift": entry.has_drift,
            "changes": entry.changes,
        }) + "\n")
    return entry


def load_diffs(env: str, limit: int = 50, base_dir: Path = DEFAULT_DIR) -> List[StoredDiff]:
    path = _store_path(base_dir, env)
    if not path.exists():
        return []
    lines = path.read_text().splitlines()
    results = []
    for line in lines[-limit:]:
        try:
            d = json.loads(line)
            results.append(StoredDiff(**d))
        except Exception:
            continue
    return results


def clear_diffs(env: str, base_dir: Path = DEFAULT_DIR) -> int:
    path = _store_path(base_dir, env)
    if not path.exists():
        return 0
    lines = path.read_text().splitlines()
    count = len(lines)
    path.unlink()
    return count

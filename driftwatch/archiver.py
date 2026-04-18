"""Archive drift reports to a compressed JSON archive."""
from __future__ import annotations

import gzip
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftReport

_DEFAULT_DIR = ".driftwatch/archives"


class ArchiverError(Exception):
    pass


@dataclass
class ArchivedReport:
    env: str
    timestamp: float
    has_drift: bool
    changes: List[dict]
    path: str = ""


def _archive_dir(base: Optional[str] = None) -> Path:
    return Path(base or _DEFAULT_DIR)


def _archive_path(env: str, ts: float, base: Optional[str] = None) -> Path:
    d = _archive_dir(base)
    d.mkdir(parents=True, exist_ok=True)
    fname = f"{env}_{int(ts)}.json.gz"
    return d / fname


def archive_report(report: DriftReport, env: str, base: Optional[str] = None) -> ArchivedReport:
    ts = time.time()
    path = _archive_path(env, ts, base)
    payload = {
        "env": env,
        "timestamp": ts,
        "has_drift": report.has_drift,
        "changes": [
            {"key": c.key, "source": c.source, "deployed": c.deployed, "kind": c.kind}
            for c in report.changes
        ],
    }
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return ArchivedReport(
        env=env,
        timestamp=ts,
        has_drift=report.has_drift,
        changes=payload["changes"],
        path=str(path),
    )


def load_archives(env: Optional[str] = None, base: Optional[str] = None) -> List[ArchivedReport]:
    d = _archive_dir(base)
    if not d.exists():
        return []
    results = []
    for f in sorted(d.glob("*.json.gz")):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                data = json.load(fh)
            if env and data.get("env") != env:
                continue
            results.append(ArchivedReport(
                env=data["env"],
                timestamp=data["timestamp"],
                has_drift=data["has_drift"],
                changes=data.get("changes", []),
                path=str(f),
            ))
        except Exception:
            continue
    return results


def clear_archives(env: Optional[str] = None, base: Optional[str] = None) -> int:
    d = _archive_dir(base)
    if not d.exists():
        return 0
    removed = 0
    for f in d.glob("*.json.gz"):
        if env:
            try:
                with gzip.open(f, "rt") as fh:
                    data = json.load(fh)
                if data.get("env") != env:
                    continue
            except Exception:
                pass
        f.unlink()
        removed += 1
    return removed

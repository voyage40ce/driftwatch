"""Baseline management for driftwatch.

Allows saving a config as a named baseline and comparing future
configs against it to detect drift over time.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASELINE_DIR_ENV = "DRIFTWATCH_BASELINE_DIR"
DEFAULT_BASELINE_DIR = ".driftwatch/baselines"


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


def _baseline_dir() -> Path:
    return Path(os.environ.get(BASELINE_DIR_ENV, DEFAULT_BASELINE_DIR))


def _baseline_path(name: str) -> Path:
    safe = name.replace(os.sep, "_")
    return _baseline_dir() / f"{safe}.json"


def save_baseline(name: str, config: dict[str, Any]) -> Path:
    """Persist *config* as a named baseline and return the file path."""
    path = _baseline_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_baseline(name: str) -> dict[str, Any]:
    """Load and return the config stored under *name*.

    Raises
    ------
    BaselineError
        If the baseline file does not exist or is malformed.
    """
    path = _baseline_path(name)
    if not path.exists():
        raise BaselineError(f"Baseline '{name}' not found at {path}")
    try:
        payload = json.loads(path.read_text())
        return payload["config"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise BaselineError(f"Baseline '{name}' is corrupt: {exc}") from exc


def list_baselines() -> list[str]:
    """Return the names of all saved baselines, sorted alphabetically."""
    directory = _baseline_dir()
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob("*.json"))


def delete_baseline(name: str) -> None:
    """Remove the named baseline file.

    Raises
    ------
    BaselineError
        If the baseline does not exist.
    """
    path = _baseline_path(name)
    if not path.exists():
        raise BaselineError(f"Baseline '{name}' not found at {path}")
    path.unlink()

"""Snapshot management for driftwatch.

Allows saving and loading configuration snapshots so that drift can be
detected against a previously-captured baseline rather than only against
a live YAML source-of-truth file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SNAPSHOT_DIR = Path(".driftwatch") / "snapshots"


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_path(name: str, directory: Path) -> Path:
    """Return the full path for a named snapshot file."""
    return directory / f"{name}.json"


def save_snapshot(
    config: dict[str, Any],
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> Path:
    """Persist *config* as a named JSON snapshot.

    Parameters
    ----------
    config:
        Flat or nested configuration dictionary to snapshot.
    name:
        Logical name for the snapshot (used as the filename stem).
    directory:
        Directory in which snapshots are stored.  Created if absent.

    Returns
    -------
    Path
        The path of the written snapshot file.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(name, directory)
    payload = {
        "name": name,
        "captured_at": datetime.now(tz=timezone.utc).isoformat(),
        "config": config,
    }
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise SnapshotError(f"Could not write snapshot '{name}': {exc}") from exc
    return path


def load_snapshot(
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> dict[str, Any]:
    """Load a previously saved snapshot and return its config dict.

    Raises
    ------
    SnapshotError
        If the snapshot file does not exist or cannot be parsed.
    """
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise SnapshotError(
            f"Snapshot '{name}' not found (looked in {directory})"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Could not read snapshot '{name}': {exc}") from exc
    return payload["config"]


def list_snapshots(directory: Path = DEFAULT_SNAPSHOT_DIR) -> list[str]:
    """Return the names of all snapshots stored in *directory*."""
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob("*.json"))

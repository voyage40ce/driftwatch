"""pinner.py – pin a config snapshot as the expected baseline for an env."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_DEFAULT_DIR = Path(".driftwatch") / "pins"


class PinnerError(Exception):
    pass


@dataclass
class PinnedConfig:
    env: str
    config: Dict[str, Any]
    pinned_at: float = field(default_factory=time.time)
    note: str = ""


def _pin_path(env: str, pins_dir: Path) -> Path:
    return pins_dir / f"{env}.json"


def pin_config(
    env: str,
    config: Dict[str, Any],
    note: str = "",
    pins_dir: Path = _DEFAULT_DIR,
) -> PinnedConfig:
    """Persist *config* as the pinned baseline for *env*."""
    pins_dir.mkdir(parents=True, exist_ok=True)
    entry = PinnedConfig(env=env, config=config, note=note)
    _pin_path(env, pins_dir).write_text(
        json.dumps(
            {"env": entry.env, "config": entry.config, "pinned_at": entry.pinned_at, "note": entry.note},
            indent=2,
        )
    )
    return entry


def load_pin(env: str, pins_dir: Path = _DEFAULT_DIR) -> PinnedConfig:
    path = _pin_path(env, pins_dir)
    if not path.exists():
        raise PinnerError(f"No pin found for env '{env}'")
    data = json.loads(path.read_text())
    return PinnedConfig(
        env=data["env"],
        config=data["config"],
        pinned_at=data.get("pinned_at", 0.0),
        note=data.get("note", ""),
    )


def list_pins(pins_dir: Path = _DEFAULT_DIR) -> List[str]:
    if not pins_dir.exists():
        return []
    return sorted(p.stem for p in pins_dir.glob("*.json"))


def delete_pin(env: str, pins_dir: Path = _DEFAULT_DIR) -> bool:
    path = _pin_path(env, pins_dir)
    if not path.exists():
        return False
    path.unlink()
    return True

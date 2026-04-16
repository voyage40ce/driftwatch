"""Environment profiling: capture and compare runtime environment metadata."""
from __future__ import annotations

import json
import os
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROFILE_DIR = Path(".driftwatch") / "profiles"


class ProfilerError(Exception):
    pass


@dataclass
class EnvProfile:
    env: str
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


def _profile_path(env: str) -> Path:
    return PROFILE_DIR / f"{env}.profile.json"


def capture_profile(env: str, extra: dict[str, Any] | None = None) -> EnvProfile:
    """Capture current runtime metadata as a profile for *env*."""
    meta: dict[str, Any] = {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "hostname": platform.node(),
        "env_vars": {k: v for k, v in os.environ.items() if k.startswith("APP_")},
    }
    if extra:
        meta.update(extra)
    return EnvProfile(env=env, timestamp=time.time(), metadata=meta)


def save_profile(profile: EnvProfile) -> Path:
    """Persist *profile* to disk, return the path written."""
    path = _profile_path(profile.env)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"env": profile.env, "timestamp": profile.timestamp, "metadata": profile.metadata}
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_profile(env: str) -> EnvProfile:
    """Load a previously saved profile for *env*."""
    path = _profile_path(env)
    if not path.exists():
        raise ProfilerError(f"No profile found for env '{env}'")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ProfilerError(f"Corrupt profile for '{env}': {exc}") from exc
    return EnvProfile(env=data["env"], timestamp=data["timestamp"], metadata=data["metadata"])


def diff_profiles(a: EnvProfile, b: EnvProfile) -> dict[str, Any]:
    """Return keys that differ between two profiles' metadata."""
    changes: dict[str, Any] = {}
    all_keys = set(a.metadata) | set(b.metadata)
    for key in all_keys:
        va, vb = a.metadata.get(key), b.metadata.get(key)
        if va != vb:
            changes[key] = {"before": va, "after": vb}
    return changes

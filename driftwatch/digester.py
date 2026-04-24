"""digester.py – Compute and compare config digests (checksums).

A digest is a stable SHA-256 fingerprint of a flattened config dict.
Useful for quickly detecting whether two configs differ without running
a full diff, and for storing a lightweight "last-known-good" hash.
"""
from __future__ import annotations

import hashlib
import json
import dataclasses
from pathlib import Path
from typing import Any

from driftwatch.differ import DriftReport


class DigesterError(Exception):
    """Raised when digest operations fail."""


@dataclasses.dataclass(frozen=True)
class ConfigDigest:
    env: str
    hexdigest: str
    key_count: int


def _stable_json(config: dict[str, Any]) -> str:
    """Return a deterministic JSON string for *config*."""
    return json.dumps(config, sort_keys=True, default=str)


def compute_digest(env: str, config: dict[str, Any]) -> ConfigDigest:
    """Return a :class:`ConfigDigest` for *config*."""
    if not isinstance(config, dict):
        raise DigesterError(f"config must be a dict, got {type(config).__name__}")
    payload = _stable_json(config).encode()
    hexdigest = hashlib.sha256(payload).hexdigest()
    return ConfigDigest(env=env, hexdigest=hexdigest, key_count=len(config))


def digests_match(a: ConfigDigest, b: ConfigDigest) -> bool:
    """Return True when both digests share the same hexdigest."""
    return a.hexdigest == b.hexdigest


def _digest_path(store_dir: Path, env: str) -> Path:
    return store_dir / f"{env}.digest.json"


def save_digest(digest: ConfigDigest, store_dir: Path) -> Path:
    """Persist *digest* under *store_dir* and return the file path."""
    store_dir.mkdir(parents=True, exist_ok=True)
    path = _digest_path(store_dir, digest.env)
    path.write_text(json.dumps(dataclasses.asdict(digest), indent=2))
    return path


def load_digest(env: str, store_dir: Path) -> ConfigDigest:
    """Load a previously saved digest for *env*."""
    path = _digest_path(store_dir, env)
    if not path.exists():
        raise DigesterError(f"No digest found for env '{env}' in {store_dir}")
    data = json.loads(path.read_text())
    return ConfigDigest(**data)


def digest_from_report(report: DriftReport) -> tuple[ConfigDigest, ConfigDigest]:
    """Derive source and live digests from a :class:`DriftReport`.

    Returns ``(source_digest, live_digest)``.
    """
    src = compute_digest(f"{report.env}:source", report.source)
    live = compute_digest(f"{report.env}:live", report.live)
    return src, live

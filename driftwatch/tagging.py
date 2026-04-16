"""Tag management for drift reports — attach arbitrary key/value metadata to environments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

TAGS_FILENAME = "tags.json"


class TagError(Exception):
    """Raised when tag operations fail."""


def _tags_path(store_dir: Path) -> Path:
    return store_dir / TAGS_FILENAME


def load_tags(store_dir: Path) -> Dict[str, Dict[str, str]]:
    """Load all tags from *store_dir*. Returns mapping of env -> {key: value}."""
    path = _tags_path(store_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file: {exc}") from exc


def save_tags(store_dir: Path, tags: Dict[str, Dict[str, str]]) -> None:
    """Persist *tags* to *store_dir*."""
    store_dir.mkdir(parents=True, exist_ok=True)
    _tags_path(store_dir).write_text(json.dumps(tags, indent=2))


def set_tag(store_dir: Path, env: str, key: str, value: str) -> None:
    """Set a single tag *key*=*value* for *env*."""
    tags = load_tags(store_dir)
    tags.setdefault(env, {})[key] = value
    save_tags(store_dir, tags)


def delete_tag(store_dir: Path, env: str, key: str) -> bool:
    """Remove *key* from *env* tags. Returns True if the key existed."""
    tags = load_tags(store_dir)
    env_tags = tags.get(env, {})
    if key not in env_tags:
        return False
    del env_tags[key]
    if not env_tags:
        del tags[env]
    save_tags(store_dir, tags)
    return True


def get_tags(store_dir: Path, env: str) -> Dict[str, str]:
    """Return all tags for *env* (empty dict if none)."""
    return load_tags(store_dir).get(env, {})


def list_envs(store_dir: Path) -> List[str]:
    """Return sorted list of environments that have tags."""
    return sorted(load_tags(store_dir).keys())

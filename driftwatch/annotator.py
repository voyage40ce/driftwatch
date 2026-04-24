"""annotator.py – attach free-text annotations to drift report items."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

ANNOTATION_FILENAME = "annotations.json"


class AnnotatorError(Exception):
    """Raised when annotation operations fail."""


@dataclass
class Annotation:
    key: str
    note: str
    author: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "note": self.note,
            "author": self.author,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(d: dict) -> "Annotation":
        return Annotation(
            key=d["key"],
            note=d["note"],
            author=d["author"],
            timestamp=float(d["timestamp"]),
        )


def _annotations_path(store_dir: str, env: str) -> str:
    return os.path.join(store_dir, env, ANNOTATION_FILENAME)


def add_annotation(
    store_dir: str, env: str, key: str, note: str, author: str
) -> Annotation:
    """Append an annotation for *key* in *env*. Returns the new Annotation."""
    annotations = load_annotations(store_dir, env)
    entry = Annotation(key=key, note=note, author=author)
    annotations.append(entry)
    _persist(store_dir, env, annotations)
    return entry


def load_annotations(
    store_dir: str, env: str, key: Optional[str] = None
) -> List[Annotation]:
    """Load annotations for *env*, optionally filtered to *key*."""
    path = _annotations_path(store_dir, env)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw: List[dict] = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise AnnotatorError(f"Cannot read annotations: {exc}") from exc
    entries = [Annotation.from_dict(r) for r in raw]
    if key is not None:
        entries = [a for a in entries if a.key == key]
    return entries


def clear_annotations(store_dir: str, env: str) -> int:
    """Delete all annotations for *env*. Returns count removed."""
    existing = load_annotations(store_dir, env)
    count = len(existing)
    path = _annotations_path(store_dir, env)
    if os.path.exists(path):
        os.remove(path)
    return count


def _persist(store_dir: str, env: str, annotations: List[Annotation]) -> None:
    env_dir = os.path.join(store_dir, env)
    os.makedirs(env_dir, exist_ok=True)
    path = _annotations_path(store_dir, env)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([a.to_dict() for a in annotations], fh, indent=2)

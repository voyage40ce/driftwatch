"""Tests for driftwatch.annotator."""
from __future__ import annotations

import json
import os

import pytest

from driftwatch.annotator import (
    Annotation,
    AnnotatorError,
    add_annotation,
    clear_annotations,
    load_annotations,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "annotations")


# ---------------------------------------------------------------------------
# add_annotation
# ---------------------------------------------------------------------------

def test_add_annotation_returns_annotation(store):
    ann = add_annotation(store, "prod", "db.host", "check this", "alice")
    assert isinstance(ann, Annotation)
    assert ann.key == "db.host"
    assert ann.note == "check this"
    assert ann.author == "alice"


def test_add_annotation_creates_file(store):
    add_annotation(store, "prod", "db.host", "note", "bob")
    path = os.path.join(store, "prod", "annotations.json")
    assert os.path.isfile(path)


def test_add_annotation_persists_multiple(store):
    add_annotation(store, "prod", "db.host", "first", "alice")
    add_annotation(store, "prod", "db.port", "second", "bob")
    entries = load_annotations(store, "prod")
    assert len(entries) == 2


def test_add_annotation_records_timestamp(store):
    import time
    before = time.time()
    ann = add_annotation(store, "prod", "x", "y", "z")
    after = time.time()
    assert before <= ann.timestamp <= after


# ---------------------------------------------------------------------------
# load_annotations
# ---------------------------------------------------------------------------

def test_load_annotations_missing_dir_returns_empty(store):
    result = load_annotations(store, "staging")
    assert result == []


def test_load_annotations_filters_by_key(store):
    add_annotation(store, "prod", "db.host", "note1", "alice")
    add_annotation(store, "prod", "db.port", "note2", "bob")
    result = load_annotations(store, "prod", key="db.host")
    assert len(result) == 1
    assert result[0].key == "db.host"


def test_load_annotations_invalid_json_raises(store):
    env_dir = os.path.join(store, "prod")
    os.makedirs(env_dir, exist_ok=True)
    path = os.path.join(env_dir, "annotations.json")
    with open(path, "w") as fh:
        fh.write("not-json")
    with pytest.raises(AnnotatorError):
        load_annotations(store, "prod")


# ---------------------------------------------------------------------------
# clear_annotations
# ---------------------------------------------------------------------------

def test_clear_annotations_returns_count(store):
    add_annotation(store, "prod", "a", "n", "u")
    add_annotation(store, "prod", "b", "n", "u")
    count = clear_annotations(store, "prod")
    assert count == 2


def test_clear_annotations_removes_file(store):
    add_annotation(store, "prod", "a", "n", "u")
    clear_annotations(store, "prod")
    path = os.path.join(store, "prod", "annotations.json")
    assert not os.path.exists(path)


def test_clear_annotations_missing_env_returns_zero(store):
    count = clear_annotations(store, "ghost")
    assert count == 0


# ---------------------------------------------------------------------------
# Annotation round-trip
# ---------------------------------------------------------------------------

def test_annotation_to_dict_and_from_dict_roundtrip():
    ann = Annotation(key="k", note="n", author="a", timestamp=1234.5)
    restored = Annotation.from_dict(ann.to_dict())
    assert restored.key == ann.key
    assert restored.note == ann.note
    assert restored.author == ann.author
    assert restored.timestamp == ann.timestamp

"""Tests for driftwatch.tagging."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from driftwatch.tagging import (
    TagError,
    delete_tag,
    get_tags,
    list_envs,
    load_tags,
    set_tag,
)


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    return tmp_path / "tags"


def test_load_tags_missing_dir_returns_empty(store):
    assert load_tags(store) == {}


def test_set_tag_creates_file(store):
    set_tag(store, "prod", "owner", "alice")
    assert (store / "tags.json").exists()


def test_set_tag_stores_value(store):
    set_tag(store, "prod", "owner", "alice")
    assert get_tags(store, "prod") == {"owner": "alice"}


def test_set_tag_multiple_envs(store):
    set_tag(store, "prod", "tier", "gold")
    set_tag(store, "staging", "tier", "silver")
    assert get_tags(store, "prod") == {"tier": "gold"}
    assert get_tags(store, "staging") == {"tier": "silver"}


def test_set_tag_overwrites_existing(store):
    set_tag(store, "prod", "owner", "alice")
    set_tag(store, "prod", "owner", "bob")
    assert get_tags(store, "prod")["owner"] == "bob"


def test_delete_tag_returns_true_when_removed(store):
    set_tag(store, "prod", "owner", "alice")
    assert delete_tag(store, "prod", "owner") is True


def test_delete_tag_removes_key(store):
    set_tag(store, "prod", "owner", "alice")
    delete_tag(store, "prod", "owner")
    assert "owner" not in get_tags(store, "prod")


def test_delete_tag_removes_env_when_empty(store):
    set_tag(store, "prod", "owner", "alice")
    delete_tag(store, "prod", "owner")
    assert "prod" not in load_tags(store)


def test_delete_tag_returns_false_when_missing(store):
    assert delete_tag(store, "prod", "nonexistent") is False


def test_list_envs_returns_sorted(store):
    set_tag(store, "staging", "k", "v")
    set_tag(store, "prod", "k", "v")
    assert list_envs(store) == ["prod", "staging"]


def test_load_tags_raises_on_corrupt_file(store):
    store.mkdir(parents=True)
    (store / "tags.json").write_text("not json{{{")
    with pytest.raises(TagError):
        load_tags(store)

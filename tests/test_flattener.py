"""Tests for driftwatch.flattener."""
import pytest

from driftwatch.flattener import (
    FlattenerError,
    FlatEntry,
    FlatResult,
    flatten_config,
    format_flat_summary,
)


# ---------------------------------------------------------------------------
# flatten_config
# ---------------------------------------------------------------------------

def test_flatten_empty_dict_returns_empty_result():
    result = flatten_config({}, env="test")
    assert isinstance(result, FlatResult)
    assert result.key_count == 0
    assert result.env == "test"


def test_flatten_flat_dict_single_depth():
    result = flatten_config({"a": 1, "b": "hello"}, env="prod")
    assert result.key_count == 2
    keys = {e.key for e in result.entries}
    assert keys == {"a", "b"}


def test_flatten_nested_dict_uses_dot_notation():
    config = {"db": {"host": "localhost", "port": 5432}}
    result = flatten_config(config, env="staging")
    keys = {e.key for e in result.entries}
    assert "db.host" in keys
    assert "db.port" in keys


def test_flatten_deeply_nested():
    config = {"a": {"b": {"c": 42}}}
    result = flatten_config(config)
    assert result.key_count == 1
    entry = result.entries[0]
    assert entry.key == "a.b.c"
    assert entry.value == 42


def test_flatten_depth_is_recorded():
    config = {"top": "val", "nested": {"inner": "v"}}
    result = flatten_config(config)
    by_key = {e.key: e for e in result.entries}
    assert by_key["top"].depth == 0
    assert by_key["nested.inner"].depth == 1


def test_flatten_custom_separator():
    config = {"db": {"host": "localhost"}}
    result = flatten_config(config, sep="/")
    assert result.entries[0].key == "db/host"


def test_flatten_non_dict_raises():
    with pytest.raises(FlattenerError, match="config must be a dict"):
        flatten_config(["not", "a", "dict"])


def test_flatten_nested_non_dict_value_raises():
    # A nested value that is itself not a dict but wrapped in one is fine;
    # only an intermediate non-dict (i.e. list) used as a sub-mapping raises.
    config = {"key": [1, 2, 3]}
    # Lists are treated as leaf values, not dicts – should NOT raise.
    result = flatten_config(config)
    assert result.entries[0].value == [1, 2, 3]


# ---------------------------------------------------------------------------
# FlatResult helpers
# ---------------------------------------------------------------------------

def test_as_dict_returns_flat_mapping():
    config = {"x": 1, "y": {"z": 2}}
    result = flatten_config(config)
    d = result.as_dict()
    assert d["x"] == 1
    assert d["y.z"] == 2


def test_key_count_matches_leaf_count():
    config = {"a": 1, "b": {"c": 2, "d": 3}}
    result = flatten_config(config)
    assert result.key_count == 3


# ---------------------------------------------------------------------------
# format_flat_summary
# ---------------------------------------------------------------------------

def test_format_flat_summary_contains_env_name():
    result = flatten_config({"k": "v"}, env="myenv")
    summary = format_flat_summary(result)
    assert "myenv" in summary


def test_format_flat_summary_contains_key():
    result = flatten_config({"db": {"host": "localhost"}}, env="prod")
    summary = format_flat_summary(result)
    assert "db.host" in summary
    assert "localhost" in summary

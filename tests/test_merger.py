"""Tests for driftwatch.merger."""
import pytest
from driftwatch.merger import (
    MergerError,
    MergeResult,
    merge_configs,
    format_merge_summary,
)


def test_merge_disjoint_keys():
    result = merge_configs({"a": 1}, {"b": 2})
    assert result.merged == {"a": 1, "b": 2}
    assert not result.has_conflicts


def test_merge_identical_no_conflict():
    result = merge_configs({"x": 10}, {"x": 10})
    assert result.merged == {"x": 10}
    assert result.conflicts == []


def test_merge_override_wins_on_conflict():
    result = merge_configs({"x": 1}, {"x": 99})
    assert result.merged["x"] == 99
    assert "x" in result.conflicts


def test_merge_nested_dicts_recursively():
    base = {"db": {"host": "localhost", "port": 5432}}
    override = {"db": {"port": 5433}}
    result = merge_configs(base, override)
    assert result.merged["db"]["host"] == "localhost"
    assert result.merged["db"]["port"] == 5433
    assert "db.port" in result.conflicts


def test_merge_nested_no_conflict_when_same():
    base = {"db": {"host": "localhost"}}
    override = {"db": {"host": "localhost"}}
    result = merge_configs(base, override)
    assert not result.has_conflicts


def test_merge_override_adds_nested_key():
    base = {"db": {"host": "localhost"}}
    override = {"db": {"port": 5432}}
    result = merge_configs(base, override)
    assert result.merged["db"] == {"host": "localhost", "port": 5432}
    assert not result.has_conflicts


def test_merge_raises_on_non_dict_base():
    with pytest.raises(MergerError):
        merge_configs("not-a-dict", {})


def test_merge_raises_on_non_dict_override():
    with pytest.raises(MergerError):
        merge_configs({}, ["list"])


def test_format_merge_summary_no_conflicts():
    result = MergeResult(merged={"a": 1})
    summary = format_merge_summary(result)
    assert "No conflicts" in summary


def test_format_merge_summary_with_conflicts():
    result = MergeResult(merged={"a": 2}, conflicts=["a", "b.c"])
    summary = format_merge_summary(result)
    assert "Conflicts (2)" in summary
    assert "! a" in summary
    assert "! b.c" in summary

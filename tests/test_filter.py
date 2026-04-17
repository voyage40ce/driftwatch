"""Tests for driftwatch.filter"""
import pytest
from driftwatch.differ import DriftReport, DriftItem
from driftwatch.filter import FilterOptions, filter_report, _matches_any


def _report(*items):
    return DriftReport(items=list(items), env="test")


def _item(key, kind="changed", old=None, new=None):
    return DriftItem(key=key, kind=kind, old_value=old, new_value=new)


def test_no_options_returns_all_items():
    r = _report(_item("a"), _item("b"))
    assert filter_report(r).items == r.items


def test_include_pattern_keeps_matching():
    r = _report(_item("db.host"), _item("app.port"))
    opts = FilterOptions(include=["db.*"])
    result = filter_report(r, opts)
    assert len(result.items) == 1
    assert result.items[0].key == "db.host"


def test_exclude_pattern_removes_matching():
    r = _report(_item("db.password"), _item("app.name"))
    opts = FilterOptions(exclude=["*.password"])
    result = filter_report(r, opts)
    assert len(result.items) == 1
    assert result.items[0].key == "app.name"


def test_changed_only_filters_kinds():
    r = _report(_item("a", "changed"), _item("b", "added"), _item("c", "removed"))
    opts = FilterOptions(changed_only=True)
    result = filter_report(r, opts)
    assert all(i.kind == "changed" for i in result.items)


def test_added_only_filters_kinds():
    r = _report(_item("a", "changed"), _item("b", "added"))
    opts = FilterOptions(added_only=True)
    result = filter_report(r, opts)
    assert len(result.items) == 1 and result.items[0].kind == "added"


def test_removed_only_filters_kinds():
    r = _report(_item("a", "removed"), _item("b", "added"))
    opts = FilterOptions(removed_only=True)
    result = filter_report(r, opts)
    assert len(result.items) == 1 and result.items[0].kind == "removed"


def test_include_and_exclude_combined():
    r = _report(_item("db.host"), _item("db.password"), _item("app.name"))
    opts = FilterOptions(include=["db.*"], exclude=["*.password"])
    result = filter_report(r, opts)
    assert len(result.items) == 1
    assert result.items[0].key == "db.host"


def test_empty_report_returns_empty():
    r = _report()
    assert filter_report(r, FilterOptions(include=["*"])).items == []


def test_matches_any_true():
    assert _matches_any("db.host", ["db.*"])


def test_matches_any_false():
    assert not _matches_any("app.port", ["db.*"])

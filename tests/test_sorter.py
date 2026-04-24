"""Tests for driftwatch.sorter."""
import pytest

from driftwatch.differ import DriftReport
from driftwatch.sorter import (
    SortOptions,
    SorterError,
    format_sort_summary,
    sort_report,
)


def _report(*items):
    return DriftReport(
        env="test",
        source={},
        deployed={},
        items=list(items),
    )


def _chg(key, change_type="changed"):
    return {"key": key, "change_type": change_type, "source_value": 1, "deployed_value": 2}


# ---------------------------------------------------------------------------
# sort by key
# ---------------------------------------------------------------------------

def test_sort_by_key_ascending():
    report = _report(_chg("zebra"), _chg("apple"), _chg("mango"))
    result = sort_report(report, SortOptions(key="key", order="asc"))
    assert [i["key"] for i in result.items] == ["apple", "mango", "zebra"]


def test_sort_by_key_descending():
    report = _report(_chg("zebra"), _chg("apple"), _chg("mango"))
    result = sort_report(report, SortOptions(key="key", order="desc"))
    assert [i["key"] for i in result.items] == ["zebra", "mango", "apple"]


# ---------------------------------------------------------------------------
# sort by change_type
# ---------------------------------------------------------------------------

def test_sort_by_change_type_ascending():
    report = _report(_chg("b", "removed"), _chg("a", "added"), _chg("c", "changed"))
    result = sort_report(report, SortOptions(key="change_type", order="asc"))
    types = [i["change_type"] for i in result.items]
    assert types == ["changed", "added", "removed"]


# ---------------------------------------------------------------------------
# sort by severity
# ---------------------------------------------------------------------------

def test_sort_by_severity_ascending():
    sev_map = {"a": "low", "b": "high", "c": "medium"}
    report = _report(_chg("a"), _chg("b"), _chg("c"))
    result = sort_report(report, SortOptions(key="severity", order="asc", severity_map=sev_map))
    assert [i["key"] for i in result.items] == ["b", "c", "a"]


def test_sort_by_severity_unknown_key_goes_last():
    sev_map = {"b": "high"}
    report = _report(_chg("a"), _chg("b"))
    result = sort_report(report, SortOptions(key="severity", order="asc", severity_map=sev_map))
    assert result.items[0]["key"] == "b"


# ---------------------------------------------------------------------------
# original report not mutated
# ---------------------------------------------------------------------------

def test_sort_does_not_mutate_original():
    original_items = [_chg("z"), _chg("a")]
    report = _report(*original_items)
    sort_report(report, SortOptions(key="key", order="asc"))
    assert report.items[0]["key"] == "z"


# ---------------------------------------------------------------------------
# default options
# ---------------------------------------------------------------------------

def test_sort_default_options_sorts_by_key_ascending():
    report = _report(_chg("z"), _chg("a"))
    result = sort_report(report)
    assert result.items[0]["key"] == "a"


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_sort_non_report_raises():
    with pytest.raises(SorterError):
        sort_report({"not": "a report"})  # type: ignore


# ---------------------------------------------------------------------------
# format_sort_summary
# ---------------------------------------------------------------------------

def test_format_sort_summary_ascending():
    report = _report(_chg("a"), _chg("b"))
    opts = SortOptions(key="key", order="asc")
    summary = format_sort_summary(report, opts)
    assert "2 item(s)" in summary
    assert "ascending" in summary
    assert "'key'" in summary


def test_format_sort_summary_descending():
    report = _report(_chg("a"))
    opts = SortOptions(key="severity", order="desc")
    summary = format_sort_summary(report, opts)
    assert "descending" in summary
    assert "'severity'" in summary

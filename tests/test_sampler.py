"""Tests for driftwatch.sampler."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.sampler import (
    SamplerError,
    SampleResult,
    format_sample_summary,
    sample_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _change(key: str, change_type: str = "changed", old="a", new="b"):
    """Return a minimal change-like object accepted by DriftReport."""
    from driftwatch.differ import DriftReport  # noqa: F401 – confirm import
    # DriftReport.changes is a list of namedtuple/dataclass from differ.diff()
    # We build one via the public diff() helper to stay implementation-agnostic.
    from driftwatch.differ import diff
    base = {key: old}
    live = {key: new} if change_type == "changed" else ({key: new} if change_type == "added" else {})
    if change_type == "removed":
        base = {key: old}
        live = {}
    elif change_type == "added":
        base = {}
        live = {key: new}
    return diff("test-env", base, live)


def _report_with_n_changes(n: int) -> DriftReport:
    """Build a DriftReport that has exactly *n* changed keys."""
    from driftwatch.differ import diff
    base = {f"key{i}": f"old{i}" for i in range(n)}
    live = {f"key{i}": f"new{i}" for i in range(n)}
    return diff("staging", base, live)


# ---------------------------------------------------------------------------
# sample_report
# ---------------------------------------------------------------------------

def test_sample_report_returns_sample_result():
    report = _report_with_n_changes(5)
    result = sample_report(report, n=3, seed=0)
    assert isinstance(result, SampleResult)


def test_sample_report_env_matches_report():
    report = _report_with_n_changes(4)
    result = sample_report(report, n=2, seed=1)
    assert result.env == "staging"


def test_sample_report_respects_n():
    report = _report_with_n_changes(10)
    result = sample_report(report, n=4, seed=42)
    assert result.sample_count == 4


def test_sample_report_n_larger_than_items_returns_all():
    report = _report_with_n_changes(3)
    result = sample_report(report, n=100, seed=7)
    assert result.sample_count == 3
    assert result.total_items == 3


def test_sample_report_seed_is_reproducible():
    report = _report_with_n_changes(8)
    r1 = sample_report(report, n=4, seed=99)
    r2 = sample_report(report, n=4, seed=99)
    assert [i.key for i in r1.sampled_items] == [i.key for i in r2.sampled_items]


def test_sample_report_different_seeds_may_differ():
    report = _report_with_n_changes(10)
    r1 = sample_report(report, n=5, seed=1)
    r2 = sample_report(report, n=5, seed=2)
    # Not guaranteed to differ, but with 10 items and C(10,5)=252 it is very likely.
    keys1 = {i.key for i in r1.sampled_items}
    keys2 = {i.key for i in r2.sampled_items}
    assert keys1 != keys2  # probabilistically safe


def test_sample_report_invalid_n_raises():
    report = _report_with_n_changes(3)
    with pytest.raises(SamplerError, match="n must be"):
        sample_report(report, n=0)


def test_sample_report_non_report_raises():
    with pytest.raises(SamplerError, match="DriftReport"):
        sample_report({"key": "value"}, n=1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# format_sample_summary
# ---------------------------------------------------------------------------

def test_format_summary_contains_env():
    report = _report_with_n_changes(2)
    result = sample_report(report, n=2, seed=0)
    summary = format_sample_summary(result)
    assert "staging" in summary


def test_format_summary_shows_seed_when_provided():
    report = _report_with_n_changes(2)
    result = sample_report(report, n=1, seed=123)
    summary = format_sample_summary(result)
    assert "123" in summary


def test_format_summary_no_seed_omits_seed_line():
    report = _report_with_n_changes(2)
    result = sample_report(report, n=1, seed=None)
    summary = format_sample_summary(result)
    assert "Seed" not in summary


def test_format_summary_empty_report_shows_no_items_message():
    from driftwatch.differ import diff
    report = diff("prod", {"a": 1}, {"a": 1})  # identical – no drift
    result = sample_report(report, n=5, seed=0)
    summary = format_sample_summary(result)
    assert "no drift items" in summary

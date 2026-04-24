"""Tests for driftwatch.deduplicator."""

import pytest

from driftwatch.differ import DriftReport
from driftwatch.deduplicator import (
    DeduplicateResult,
    DeduplicatorError,
    deduplicate,
    format_dedup_summary,
    has_duplicates,
)


def _report(
    changes=None,
    added=None,
    removed=None,
) -> DriftReport:
    return DriftReport(
        changes=changes or [],
        added=added or [],
        removed=removed or [],
    )


def test_empty_reports_raises():
    with pytest.raises(DeduplicatorError):
        deduplicate([])


def test_single_report_no_duplicates():
    report = _report(
        changes=[("db.host", "old", "new")],
        added=[("db.port", 5432)],
        removed=[("db.name", "mydb")],
    )
    result = deduplicate([report])
    assert len(result.unique_changes) == 1
    assert len(result.unique_added) == 1
    assert len(result.unique_removed) == 1
    assert result.duplicate_count == 0


def test_two_identical_reports_deduplicates():
    report = _report(
        changes=[("key", "a", "b")],
        added=[("x", 1)],
        removed=[("y", 2)],
    )
    result = deduplicate([report, report])
    assert len(result.unique_changes) == 1
    assert len(result.unique_added) == 1
    assert len(result.unique_removed) == 1
    assert result.duplicate_count == 3


def test_disjoint_reports_merged():
    r1 = _report(changes=[("a", 1, 2)])
    r2 = _report(changes=[("b", 3, 4)])
    result = deduplicate([r1, r2])
    assert len(result.unique_changes) == 2
    assert result.duplicate_count == 0


def test_partial_overlap_counted_correctly():
    r1 = _report(added=[("k", "v"), ("m", "n")])
    r2 = _report(added=[("k", "v"), ("p", "q")])
    result = deduplicate([r1, r2])
    assert len(result.unique_added) == 3  # k, m, p
    assert result.duplicate_count == 1


def test_has_duplicates_true():
    report = _report(changes=[("x", 0, 1)])
    result = deduplicate([report, report])
    assert has_duplicates(result) is True


def test_has_duplicates_false():
    result = DeduplicateResult()
    assert has_duplicates(result) is False


def test_format_dedup_summary_contains_counts():
    report = _report(
        changes=[("a", 1, 2)],
        added=[("b", 3)],
        removed=[("c", 4)],
    )
    result = deduplicate([report])
    summary = format_dedup_summary(result)
    assert "Unique drift items : 3" in summary
    assert "Duplicates removed : 0" in summary


def test_format_dedup_summary_shows_duplicates():
    report = _report(removed=[("z", 99)])
    result = deduplicate([report, report])
    summary = format_dedup_summary(result)
    assert "Duplicates removed : 1" in summary

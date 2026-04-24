"""Tests for driftwatch.splitter."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport
from driftwatch.splitter import (
    SplitResult,
    SplitterError,
    format_split_summary,
    split_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _change(key: str, src=None, dep=None, ctype="changed"):
    """Build a minimal Change-like object accepted by DriftReport."""
    from driftwatch.differ import diff  # noqa: PLC0415

    # Use the real diff function to obtain a properly typed Change object.
    if ctype == "changed":
        source = {key: src}
        deployed = {key: dep}
    elif ctype == "added":
        source = {}
        deployed = {key: dep}
    else:  # removed
        source = {key: src}
        deployed = {}
    return diff(source, deployed).changes


def _prefixed_report(*pairs):
    """Build a DriftReport whose keys are prefixed with an env name.

    Each item in *pairs* is (env, key, src, dep).
    """
    from driftwatch.differ import diff  # noqa: PLC0415

    source, deployed = {}, {}
    for env, key, src, dep in pairs:
        full = f"{env}.{key}"
        source[full] = src
        deployed[full] = dep
    return diff(source, deployed)


# ---------------------------------------------------------------------------
# split_report
# ---------------------------------------------------------------------------

def test_split_empty_report_returns_empty_result():
    report = DriftReport(changes=[])
    result = split_report(report)
    assert result.reports == {}


def test_split_raises_on_non_report():
    with pytest.raises(SplitterError):
        split_report({})  # type: ignore[arg-type]


def test_split_single_env_all_keys_in_bucket():
    report = _prefixed_report(
        ("staging", "db.host", "old", "new"),
        ("staging", "db.port", 5432, 5433),
    )
    result = split_report(report)
    assert result.environments() == ["staging"]
    assert len(result.reports["staging"].changes) == 2


def test_split_multiple_envs_separated_correctly():
    report = _prefixed_report(
        ("prod", "api.key", "abc", "xyz"),
        ("dev", "api.key", "abc", "xyz"),
        ("prod", "cache.ttl", 60, 120),
    )
    result = split_report(report)
    assert set(result.environments()) == {"prod", "dev"}
    assert len(result.reports["prod"].changes) == 2
    assert len(result.reports["dev"].changes) == 1


def test_split_strips_env_prefix_from_keys():
    report = _prefixed_report(("prod", "database.host", "a", "b"))
    result = split_report(report)
    keys = [c.key for c in result.reports["prod"].changes]
    assert all(not k.startswith("prod.") for k in keys)
    assert "database.host" in keys


def test_split_global_bucket_for_unprefixed_keys():
    from driftwatch.differ import diff  # noqa: PLC0415

    report = diff({"plain_key": "old"}, {"plain_key": "new"})
    result = split_report(report)
    assert "__global__" in result.environments()
    assert len(result.reports["__global__"].changes) == 1


def test_split_custom_separator():
    from driftwatch.differ import diff  # noqa: PLC0415

    report = diff({"prod::timeout": 10}, {"prod::timeout": 20})
    result = split_report(report, env_prefix_sep="::")  # type: ignore[call-arg]
    assert "prod" in result.environments()


# ---------------------------------------------------------------------------
# SplitResult.get
# ---------------------------------------------------------------------------

def test_get_known_env_returns_report():
    report = _prefixed_report(("qa", "flag", True, False))
    result = split_report(report)
    sub = result.get("qa")
    assert isinstance(sub, DriftReport)


def test_get_unknown_env_raises_key_error():
    result = SplitResult()
    with pytest.raises(KeyError):
        result.get("nonexistent")


# ---------------------------------------------------------------------------
# format_split_summary
# ---------------------------------------------------------------------------

def test_format_split_summary_empty():
    summary = format_split_summary(SplitResult())
    assert "No environments" in summary


def test_format_split_summary_shows_env_and_count():
    report = _prefixed_report(
        ("prod", "x", 1, 2),
        ("dev", "y", "a", "b"),
    )
    result = split_report(report)
    summary = format_split_summary(result)
    assert "prod" in summary
    assert "dev" in summary
    assert "1 change" in summary

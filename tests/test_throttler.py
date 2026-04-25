"""Tests for driftwatch/throttler.py."""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from typing import List

import pytest

from driftwatch.differ import DriftReport
from driftwatch.throttler import (
    ThrottleOptions,
    ThrottleResult,
    ThrottlerError,
    format_throttle_summary,
    throttle_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _change(key: str, change_type: str = "changed"):
    return SimpleNamespace(key=key, change_type=change_type, old=None, new=None)


def _report(env: str, keys: List[str]) -> DriftReport:
    changes = [_change(k) for k in keys]
    return DriftReport(env=env, changes=changes)  # type: ignore[arg-type]


@pytest.fixture()
def opts(tmp_path: Path) -> ThrottleOptions:
    return ThrottleOptions(cooldown_seconds=60, store_dir=tmp_path / "throttle")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_all_keys_pass_on_first_call(opts):
    report = _report("prod", ["a", "b", "c"])
    result = throttle_report(report, opts)
    assert result.passed == ["a", "b", "c"]
    assert result.suppressed == []


def test_state_file_created_after_first_call(opts):
    report = _report("prod", ["x"])
    throttle_report(report, opts)
    state_file = opts.store_dir / "prod.json"
    assert state_file.exists()


def test_second_call_within_cooldown_suppresses_keys(opts):
    report = _report("prod", ["key1", "key2"])
    throttle_report(report, opts)  # first pass – records timestamps
    result2 = throttle_report(report, opts)  # second pass – still within cooldown
    assert result2.suppressed == ["key1", "key2"]
    assert result2.passed == []


def test_key_passes_again_after_cooldown(opts, monkeypatch):
    report = _report("prod", ["k"])
    throttle_report(report, opts)

    # Advance time past the cooldown
    original_time = time.time()
    monkeypatch.setattr("driftwatch.throttler.time.time", lambda: original_time + 61)

    result = throttle_report(report, opts)
    assert result.passed == ["k"]
    assert result.suppressed == []


def test_env_isolation(opts):
    r_prod = _report("prod", ["k"])
    r_staging = _report("staging", ["k"])
    throttle_report(r_prod, opts)
    # staging has no prior state – key should pass
    result = throttle_report(r_staging, opts)
    assert result.passed == ["k"]


def test_empty_report_returns_empty_result(opts):
    report = _report("prod", [])
    result = throttle_report(report, opts)
    assert result.passed == []
    assert result.suppressed == []


def test_throttler_error_on_corrupt_state(opts):
    state_file = opts.store_dir / "prod.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("{invalid json")
    report = _report("prod", ["k"])
    with pytest.raises(ThrottlerError):
        throttle_report(report, opts)


def test_format_throttle_summary_shows_counts(opts):
    report = _report("prod", ["a", "b"])
    throttle_report(report, opts)  # pass first time
    result2 = throttle_report(report, opts)  # suppress second time
    summary = format_throttle_summary(result2)
    assert "suppressed: 2" in summary
    assert "passed:     0" in summary
    assert "prod" in summary


def test_result_counts_match_lists(opts):
    report = _report("prod", ["x", "y", "z"])
    result = throttle_report(report, opts)
    assert result.passed_count == len(result.passed)
    assert result.suppressed_count == len(result.suppressed)

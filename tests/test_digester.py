"""Tests for driftwatch.digester."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.digester import (
    ConfigDigest,
    DigesterError,
    compute_digest,
    digests_match,
    save_digest,
    load_digest,
    digest_from_report,
)
from driftwatch.differ import DriftReport, diff


# ---------------------------------------------------------------------------
# compute_digest
# ---------------------------------------------------------------------------

def test_compute_digest_returns_config_digest():
    d = compute_digest("prod", {"a": 1})
    assert isinstance(d, ConfigDigest)
    assert d.env == "prod"
    assert len(d.hexdigest) == 64  # SHA-256 hex


def test_compute_digest_key_count():
    d = compute_digest("prod", {"a": 1, "b": 2, "c": 3})
    assert d.key_count == 3


def test_compute_digest_identical_configs_same_hash():
    d1 = compute_digest("prod", {"x": 10, "y": 20})
    d2 = compute_digest("prod", {"y": 20, "x": 10})  # different insertion order
    assert d1.hexdigest == d2.hexdigest


def test_compute_digest_different_configs_different_hash():
    d1 = compute_digest("prod", {"x": 10})
    d2 = compute_digest("prod", {"x": 99})
    assert d1.hexdigest != d2.hexdigest


def test_compute_digest_non_dict_raises():
    with pytest.raises(DigesterError):
        compute_digest("prod", ["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# digests_match
# ---------------------------------------------------------------------------

def test_digests_match_same_content():
    d1 = compute_digest("prod", {"a": 1})
    d2 = compute_digest("staging", {"a": 1})  # different env, same content
    assert digests_match(d1, d2)


def test_digests_match_different_content():
    d1 = compute_digest("prod", {"a": 1})
    d2 = compute_digest("prod", {"a": 2})
    assert not digests_match(d1, d2)


# ---------------------------------------------------------------------------
# save_digest / load_digest
# ---------------------------------------------------------------------------

def test_save_digest_creates_file(tmp_path: Path):
    d = compute_digest("prod", {"k": "v"})
    path = save_digest(d, tmp_path)
    assert path.exists()


def test_save_digest_file_content(tmp_path: Path):
    d = compute_digest("prod", {"k": "v"})
    path = save_digest(d, tmp_path)
    data = json.loads(path.read_text())
    assert data["env"] == "prod"
    assert data["hexdigest"] == d.hexdigest
    assert data["key_count"] == 1


def test_load_digest_roundtrip(tmp_path: Path):
    d = compute_digest("staging", {"foo": "bar"})
    save_digest(d, tmp_path)
    loaded = load_digest("staging", tmp_path)
    assert loaded == d


def test_load_digest_missing_raises(tmp_path: Path):
    with pytest.raises(DigesterError, match="No digest found"):
        load_digest("nonexistent", tmp_path)


def test_save_digest_creates_store_dir(tmp_path: Path):
    store = tmp_path / "deep" / "nested"
    d = compute_digest("prod", {})
    save_digest(d, store)
    assert store.is_dir()


# ---------------------------------------------------------------------------
# digest_from_report
# ---------------------------------------------------------------------------

def test_digest_from_report_returns_two_digests():
    source = {"a": 1}
    live = {"a": 2}
    report = diff("prod", source, live)
    src_d, live_d = digest_from_report(report)
    assert isinstance(src_d, ConfigDigest)
    assert isinstance(live_d, ConfigDigest)


def test_digest_from_report_no_drift_same_hash():
    cfg = {"a": 1, "b": 2}
    report = diff("prod", cfg, cfg.copy())
    src_d, live_d = digest_from_report(report)
    assert digests_match(src_d, live_d)


def test_digest_from_report_drift_different_hash():
    report = diff("prod", {"a": 1}, {"a": 99})
    src_d, live_d = digest_from_report(report)
    assert not digests_match(src_d, live_d)

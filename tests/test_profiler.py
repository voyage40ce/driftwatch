"""Tests for driftwatch.profiler."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.profiler import (
    EnvProfile,
    ProfilerError,
    capture_profile,
    diff_profiles,
    load_profile,
    save_profile,
    _profile_path,
)


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    import driftwatch.profiler as mod
    monkeypatch.setattr(mod, "PROFILE_DIR", tmp_path / "profiles")


def test_capture_profile_returns_env_profile():
    p = capture_profile("staging")
    assert isinstance(p, EnvProfile)
    assert p.env == "staging"
    assert "python_version" in p.metadata


def test_capture_profile_includes_extra():
    p = capture_profile("prod", extra={"version": "1.2.3"})
    assert p.metadata["version"] == "1.2.3"


def test_save_profile_creates_file(tmp_path, monkeypatch):
    import driftwatch.profiler as mod
    monkeypatch.setattr(mod, "PROFILE_DIR", tmp_path / "profiles")
    p = capture_profile("dev")
    path = save_profile(p)
    assert path.exists()


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    import driftwatch.profiler as mod
    monkeypatch.setattr(mod, "PROFILE_DIR", tmp_path / "profiles")
    p = capture_profile("dev", extra={"x": 42})
    save_profile(p)
    loaded = load_profile("dev")
    assert loaded.env == "dev"
    assert loaded.metadata["x"] == 42


def test_load_profile_missing_raises(tmp_path, monkeypatch):
    import driftwatch.profiler as mod
    monkeypatch.setattr(mod, "PROFILE_DIR", tmp_path / "profiles")
    with pytest.raises(ProfilerError, match="No profile found"):
        load_profile("ghost")


def test_load_profile_corrupt_raises(tmp_path, monkeypatch):
    import driftwatch.profiler as mod
    monkeypatch.setattr(mod, "PROFILE_DIR", tmp_path / "profiles")
    path = tmp_path / "profiles" / "bad.profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json")
    with pytest.raises(ProfilerError, match="Corrupt"):
        load_profile("bad")


def test_diff_profiles_detects_changes():
    a = EnvProfile("e", 0.0, {"x": 1, "y": "hello"})
    b = EnvProfile("e", 1.0, {"x": 2, "y": "hello", "z": "new"})
    changes = diff_profiles(a, b)
    assert "x" in changes
    assert changes["x"] == {"before": 1, "after": 2}
    assert "z" in changes
    assert "y" not in changes


def test_diff_profiles_no_changes():
    a = EnvProfile("e", 0.0, {"x": 1})
    b = EnvProfile("e", 1.0, {"x": 1})
    assert diff_profiles(a, b) == {}

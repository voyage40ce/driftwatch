"""Tests for driftwatch.comparator."""

from driftwatch.profiler import EnvProfile
from driftwatch.comparator import compare_profiles, format_profile_diff, ProfileDiff


def _profile(env: str, config: dict) -> EnvProfile:
    return EnvProfile(env=env, config=config, captured_at="2024-01-01T00:00:00")


def test_no_diff_when_identical():
    a = _profile("staging", {"db": {"host": "localhost", "port": 5432}})
    b = _profile("prod", {"db": {"host": "localhost", "port": 5432}})
    diff = compare_profiles(a, b)
    assert not diff.has_diff
    assert diff.added == {}
    assert diff.removed == {}
    assert diff.changed == {}


def test_detects_added_key():
    a = _profile("staging", {"x": 1})
    b = _profile("prod", {"x": 1, "y": 2})
    diff = compare_profiles(a, b)
    assert "y" in diff.added
    assert diff.added["y"] == 2
    assert diff.has_diff


def test_detects_removed_key():
    a = _profile("staging", {"x": 1, "y": 2})
    b = _profile("prod", {"x": 1})
    diff = compare_profiles(a, b)
    assert "y" in diff.removed
    assert diff.removed["y"] == 2


def test_detects_changed_value():
    a = _profile("staging", {"db": {"port": 5432}})
    b = _profile("prod", {"db": {"port": 3306}})
    diff = compare_profiles(a, b)
    assert "db.port" in diff.changed
    assert diff.changed["db.port"] == (5432, 3306)


def test_env_names_recorded():
    a = _profile("staging", {})
    b = _profile("prod", {})
    diff = compare_profiles(a, b)
    assert diff.env_a == "staging"
    assert diff.env_b == "prod"


def test_format_no_diff():
    a = _profile("staging", {"k": 1})
    b = _profile("prod", {"k": 1})
    diff = compare_profiles(a, b)
    out = format_profile_diff(diff)
    assert "No differences" in out
    assert "staging" in out
    assert "prod" in out


def test_format_shows_changes():
    a = _profile("staging", {"k": "old"})
    b = _profile("prod", {"k": "new"})
    diff = compare_profiles(a, b)
    out = format_profile_diff(diff)
    assert "~" in out
    assert "old" in out
    assert "new" in out


def test_format_shows_added_and_removed():
    a = _profile("staging", {"only_a": 1})
    b = _profile("prod", {"only_b": 2})
    diff = compare_profiles(a, b)
    out = format_profile_diff(diff)
    assert "+" in out
    assert "-" in out

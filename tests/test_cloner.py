"""Tests for driftwatch.cloner."""
import pytest
from driftwatch.cloner import (
    ClonerError,
    CloneResult,
    clone_config,
    clone_from_file,
    format_clone_summary,
)


SOURCE = {"db": {"host": "prod-db", "port": 5432}, "debug": False}


def test_clone_returns_clone_result():
    r = clone_config(SOURCE, "prod", "staging")
    assert isinstance(r, CloneResult)
    assert r.source_env == "prod"
    assert r.target_env == "staging"


def test_clone_deep_copies_config():
    r = clone_config(SOURCE, "prod", "staging")
    r.config["db"]["host"] = "changed"
    assert SOURCE["db"]["host"] == "prod-db"


def test_clone_no_overrides_zero_applied():
    r = clone_config(SOURCE, "prod", "staging")
    assert r.overrides_applied == 0
    assert r.skipped_keys == []


def test_clone_applies_top_level_override():
    r = clone_config(SOURCE, "prod", "staging", overrides={"debug": True})
    assert r.config["debug"] is True
    assert r.overrides_applied == 1


def test_clone_applies_nested_override_dot_notation():
    r = clone_config(SOURCE, "prod", "staging", overrides={"db.host": "staging-db"})
    assert r.config["db"]["host"] == "staging-db"
    assert r.overrides_applied == 1


def test_clone_creates_missing_nested_key():
    r = clone_config(SOURCE, "prod", "staging", overrides={"cache.ttl": 60})
    assert r.config["cache"]["ttl"] == 60


def test_clone_raises_on_non_mapping_source():
    with pytest.raises(ClonerError):
        clone_config(["not", "a", "dict"], "prod", "staging")


def test_clone_raises_on_empty_target_env():
    with pytest.raises(ClonerError):
        clone_config(SOURCE, "prod", "")


def test_clone_from_file_raises_on_missing(tmp_path):
    with pytest.raises(ClonerError):
        clone_from_file(str(tmp_path / "missing.yaml"), "prod", "staging")


def test_clone_from_file_success(tmp_path):
    import yaml
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.dump(SOURCE))
    r = clone_from_file(str(p), "prod", "staging")
    assert r.config["db"]["host"] == "prod-db"


def test_format_clone_summary_no_skips():
    r = CloneResult("prod", "staging", {}, overrides_applied=2)
    out = format_clone_summary(r)
    assert "prod" in out
    assert "staging" in out
    assert "2" in out
    assert "Skipped" not in out


def test_format_clone_summary_with_skips():
    r = CloneResult("prod", "staging", {}, overrides_applied=1, skipped_keys=["bad.key"])
    out = format_clone_summary(r)
    assert "bad.key" in out

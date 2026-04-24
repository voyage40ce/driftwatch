"""Tests for driftwatch/transformer.py."""
import pytest
from driftwatch.transformer import (
    TransformRule,
    TransformerError,
    apply_transforms,
)


def _rule(name, pattern, operation, value=None):
    return TransformRule(name=name, pattern=pattern, operation=operation, value=value)


# ---------------------------------------------------------------------------
# basic operations
# ---------------------------------------------------------------------------

def test_set_operation_replaces_value():
    cfg = {"host": "localhost"}
    result = apply_transforms(cfg, [_rule("r", "^host$", "set", "prod.example.com")])
    assert result.config["host"] == "prod.example.com"


def test_delete_operation_removes_key():
    cfg = {"secret": "abc", "host": "h"}
    result = apply_transforms(cfg, [_rule("r", "^secret$", "delete")])
    assert "secret" not in result.config
    assert result.config["host"] == "h"


def test_uppercase_operation():
    cfg = {"env": "production"}
    result = apply_transforms(cfg, [_rule("r", "^env$", "uppercase")])
    assert result.config["env"] == "PRODUCTION"


def test_lowercase_operation():
    cfg = {"region": "US-EAST-1"}
    result = apply_transforms(cfg, [_rule("r", "^region$", "lowercase")])
    assert result.config["region"] == "us-east-1"


def test_prefix_operation():
    cfg = {"path": "/data"}
    result = apply_transforms(cfg, [_rule("r", "^path$", "prefix", "/mnt")])
    assert result.config["path"] == "/mnt/data"


def test_suffix_operation():
    cfg = {"name": "service"}
    result = apply_transforms(cfg, [_rule("r", "^name$", "suffix", "-v2")])
    assert result.config["name"] == "service-v2"


# ---------------------------------------------------------------------------
# nested keys
# ---------------------------------------------------------------------------

def test_nested_key_dot_notation():
    cfg = {"database": {"host": "localhost"}}
    result = apply_transforms(cfg, [_rule("r", "database\.host", "set", "db.prod")])
    assert result.config["database"]["host"] == "db.prod"


def test_pattern_matches_multiple_keys():
    cfg = {"db_host": "a", "db_port": "5432", "other": "x"}
    result = apply_transforms(cfg, [_rule("r", "^db_", "uppercase")])
    assert result.config["db_host"] == "A"
    assert result.config["db_port"] == "5432"  # int-like string uppercased stays same
    assert result.config["other"] == "x"


# ---------------------------------------------------------------------------
# applied / skipped tracking
# ---------------------------------------------------------------------------

def test_applied_list_populated():
    cfg = {"key": "val"}
    result = apply_transforms(cfg, [_rule("myrule", "^key$", "uppercase")])
    assert any("myrule" in a for a in result.applied)


def test_skipped_when_no_key_matches():
    cfg = {"foo": "bar"}
    result = apply_transforms(cfg, [_rule("ghost", "^nonexistent$", "set", "x")])
    assert "ghost" in result.skipped
    assert result.config == {"foo": "bar"}


# ---------------------------------------------------------------------------
# original config is not mutated
# ---------------------------------------------------------------------------

def test_original_config_not_mutated():
    cfg = {"key": "original"}
    apply_transforms(cfg, [_rule("r", "^key$", "set", "changed")])
    assert cfg["key"] == "original"


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_invalid_regex_raises_transformer_error():
    cfg = {"k": "v"}
    with pytest.raises(TransformerError, match="Invalid pattern"):
        apply_transforms(cfg, [_rule("bad", "[unclosed", "set", "x")])


def test_unknown_operation_raises_transformer_error():
    cfg = {"k": "v"}
    with pytest.raises(TransformerError, match="Unknown operation"):
        apply_transforms(cfg, [_rule("bad", "^k$", "explode")])


def test_empty_rules_returns_identical_config():
    cfg = {"a": 1, "b": {"c": 2}}
    result = apply_transforms(cfg, [])
    assert result.config == cfg
    assert result.applied == []
    assert result.skipped == []

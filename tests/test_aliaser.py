"""Tests for driftwatch.aliaser and driftwatch.commands.aliaser_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import yaml

from driftwatch.aliaser import (
    AliasError,
    AliasMap,
    apply_aliases,
    load_alias_map,
    resolve_aliases,
)
from driftwatch.commands.aliaser_cmd import _dispatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, data: object) -> Path:
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"aliaser_cmd": "list"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# AliasMap unit tests
# ---------------------------------------------------------------------------

def test_alias_map_add_and_retrieve():
    am = AliasMap()
    am.add("db.host", "Database Host")
    assert am.alias_for("db.host") == "Database Host"
    assert am.key_for("Database Host") == "db.host"


def test_alias_map_missing_key_returns_none():
    am = AliasMap()
    assert am.alias_for("nonexistent") is None
    assert am.key_for("nonexistent") is None


def test_alias_map_all_aliases_returns_dict():
    am = AliasMap()
    am.add("a", "Alpha")
    am.add("b", "Beta")
    assert am.all_aliases() == {"a": "Alpha", "b": "Beta"}


# ---------------------------------------------------------------------------
# load_alias_map tests
# ---------------------------------------------------------------------------

def test_load_alias_map_returns_alias_map(tmp_path):
    f = _write(tmp_path, "aliases.yaml", {"aliases": {"db.host": "DB Host"}})
    am = load_alias_map(str(f))
    assert am.alias_for("db.host") == "DB Host"


def test_load_alias_map_missing_file_raises(tmp_path):
    with pytest.raises(AliasError, match="not found"):
        load_alias_map(str(tmp_path / "missing.yaml"))


def test_load_alias_map_invalid_yaml_raises(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text(": : :")
    with pytest.raises(AliasError, match="Invalid YAML"):
        load_alias_map(str(f))


def test_load_alias_map_missing_aliases_key_raises(tmp_path):
    f = _write(tmp_path, "a.yaml", {"not_aliases": {}})
    with pytest.raises(AliasError, match="'aliases'"):
        load_alias_map(str(f))


def test_load_alias_map_non_mapping_aliases_raises(tmp_path):
    f = _write(tmp_path, "a.yaml", {"aliases": ["a", "b"]})
    with pytest.raises(AliasError, match="mapping"):
        load_alias_map(str(f))


# ---------------------------------------------------------------------------
# apply_aliases / resolve_aliases tests
# ---------------------------------------------------------------------------

def test_apply_aliases_replaces_known_keys():
    am = AliasMap()
    am.add("db.host", "Database Host")
    result = apply_aliases({"db.host": "localhost", "app.port": "8080"}, am)
    assert "Database Host" in result
    assert result["Database Host"] == "localhost"
    assert result["app.port"] == "8080"


def test_resolve_aliases_maps_back_to_canonical():
    am = AliasMap()
    am.add("db.host", "Database Host")
    result = resolve_aliases({"Database Host": "localhost"}, am)
    assert result["db.host"] == "localhost"


# ---------------------------------------------------------------------------
# CLI dispatch tests
# ---------------------------------------------------------------------------

def test_cmd_list_returns_zero(tmp_path, capsys):
    f = _write(tmp_path, "a.yaml", {"aliases": {"db.host": "DB Host"}})
    ns = _ns(aliaser_cmd="list", alias_file=str(f))
    assert _dispatch(ns) == 0
    out = capsys.readouterr().out
    assert "db.host" in out
    assert "DB Host" in out


def test_cmd_list_missing_file_returns_two(tmp_path):
    ns = _ns(aliaser_cmd="list", alias_file=str(tmp_path / "nope.yaml"))
    assert _dispatch(ns) == 2


def test_cmd_apply_returns_zero(tmp_path, capsys):
    cfg = _write(tmp_path, "cfg.yaml", {"db": {"host": "localhost"}})
    af = _write(tmp_path, "aliases.yaml", {"aliases": {"db.host": "DB Host"}})
    ns = _ns(aliaser_cmd="apply", config=str(cfg), alias_file=str(af))
    assert _dispatch(ns) == 0
    out = capsys.readouterr().out
    assert "DB Host" in out


def test_cmd_apply_missing_config_returns_two(tmp_path):
    af = _write(tmp_path, "aliases.yaml", {"aliases": {}})
    ns = _ns(aliaser_cmd="apply", config=str(tmp_path / "nope.yaml"), alias_file=str(af))
    assert _dispatch(ns) == 2

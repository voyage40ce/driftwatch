import pytest
from driftwatch.renamer import rename_config, RenamerError


def _cfg():
    return {"database": {"host": "localhost", "port": 5432}, "debug": True}


def test_rename_top_level_key():
    result = rename_config({"old": 1, "other": 2}, {"old": "new"})
    assert "new" in result.config
    assert "old" not in result.config
    assert result.config["new"] == 1
    assert "old" in result.renamed


def test_rename_nested_key_dot_notation():
    cfg = _cfg()
    result = rename_config(cfg, {"database.host": "database.hostname"})
    assert result.config["database"]["hostname"] == "localhost"
    assert "host" not in result.config["database"]
    assert "database.host" in result.renamed


def test_rename_moves_nested_to_top_level():
    cfg = {"db": {"port": 5432}}
    result = rename_config(cfg, {"db.port": "port"})
    assert result.config["port"] == 5432
    assert "port" not in result.config.get("db", {})


def test_missing_key_goes_to_skipped():
    result = rename_config({"a": 1}, {"nonexistent": "b"})
    assert "nonexistent" in result.skipped
    assert result.config == {"a": 1}


def test_destination_exists_goes_to_skipped():
    result = rename_config({"a": 1, "b": 99}, {"a": "b"})
    assert "a" in result.skipped
    assert result.config["b"] == 99
    assert result.config["a"] == 1


def test_original_config_not_mutated():
    cfg = {"x": {"y": 42}}
    original = {"x": {"y": 42}}
    rename_config(cfg, {"x.y": "x.z"})
    assert cfg == original


def test_invalid_mapping_raises():
    with pytest.raises(RenamerError):
        rename_config({}, "not-a-dict")


def test_empty_mapping_returns_unchanged():
    cfg = {"a": 1}
    result = rename_config(cfg, {})
    assert result.config == cfg
    assert result.renamed == []
    assert result.skipped == []


def test_multiple_renames():
    cfg = {"a": 1, "b": 2, "c": 3}
    result = rename_config(cfg, {"a": "alpha", "b": "beta"})
    assert result.config == {"alpha": 1, "beta": 2, "c": 3}
    assert set(result.renamed) == {"a", "b"}

"""Tests for driftwatch.scoper and driftwatch.commands.scoper_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import yaml

from driftwatch.differ import DriftReport
from driftwatch.scoper import (
    Scope,
    ScopeError,
    apply_scope,
    load_scope,
)
from driftwatch.commands.scoper_cmd import _dispatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, data: object) -> str:
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def _report(*keys, change_type: str = "changed") -> DriftReport:
    return DriftReport(
        env="test",
        source="src.yaml",
        changes=[{"key": k, "change_type": change_type, "deployed": 1, "source": 2} for k in keys],
    )


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        scope_file="", scope_name="", deployed="", source="", no_color=True, env=""
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# load_scope
# ---------------------------------------------------------------------------

def test_load_scope_returns_scope(tmp_path):
    path = _write(tmp_path, "scopes.yaml", {"scopes": {"prod": ["db.*", "cache.*"]}})
    scope = load_scope(path, "prod")
    assert scope.name == "prod"
    assert scope.patterns == ["db.*", "cache.*"]


def test_load_scope_missing_file_raises(tmp_path):
    with pytest.raises(ScopeError, match="not found"):
        load_scope(str(tmp_path / "missing.yaml"), "prod")


def test_load_scope_missing_scopes_key_raises(tmp_path):
    path = _write(tmp_path, "bad.yaml", {"other": {}})
    with pytest.raises(ScopeError, match="'scopes'"):
        load_scope(path, "prod")


def test_load_scope_unknown_name_raises(tmp_path):
    path = _write(tmp_path, "scopes.yaml", {"scopes": {"staging": ["*"]}})
    with pytest.raises(ScopeError, match="'prod'"):
        load_scope(path, "prod")


def test_load_scope_non_list_patterns_raises(tmp_path):
    path = _write(tmp_path, "scopes.yaml", {"scopes": {"prod": "db.*"}})
    with pytest.raises(ScopeError, match="list"):
        load_scope(path, "prod")


# ---------------------------------------------------------------------------
# apply_scope
# ---------------------------------------------------------------------------

def test_apply_scope_keeps_matching_keys():
    scope = Scope(name="db", patterns=["db.*"])
    report = _report("db.host", "db.port", "cache.ttl")
    result = apply_scope(report, scope)
    assert result.total_before == 3
    assert result.total_after == 2
    assert result.filtered_count == 1
    assert all(c["key"].startswith("db.") for c in result.report.changes)


def test_apply_scope_wildcard_keeps_all():
    scope = Scope(name="all", patterns=["*"])
    report = _report("a", "b", "c")
    result = apply_scope(report, scope)
    assert result.total_after == 3


def test_apply_scope_no_match_returns_empty():
    scope = Scope(name="x", patterns=["x.*"])
    report = _report("db.host", "cache.ttl")
    result = apply_scope(report, scope)
    assert result.total_after == 0


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

def test_dispatch_missing_scope_file_returns_two(tmp_path):
    deployed = _write(tmp_path, "dep.yaml", {"a": 1})
    source = _write(tmp_path, "src.yaml", {"a": 1})
    ns = _ns(scope_file=str(tmp_path / "no.yaml"), scope_name="prod", deployed=deployed, source=source)
    assert _dispatch(ns) == 2


def test_dispatch_missing_config_returns_two(tmp_path):
    scope_file = _write(tmp_path, "s.yaml", {"scopes": {"prod": ["*"]}})
    ns = _ns(scope_file=scope_file, scope_name="prod", deployed=str(tmp_path / "nope.yaml"), source=str(tmp_path / "nope2.yaml"))
    assert _dispatch(ns) == 2


def test_dispatch_no_drift_returns_zero(tmp_path):
    scope_file = _write(tmp_path, "s.yaml", {"scopes": {"prod": ["*"]}})
    deployed = _write(tmp_path, "dep.yaml", {"db": {"host": "localhost"}})
    source = _write(tmp_path, "src.yaml", {"db": {"host": "localhost"}})
    ns = _ns(scope_file=scope_file, scope_name="prod", deployed=deployed, source=source)
    assert _dispatch(ns) == 0


def test_dispatch_drift_in_scope_returns_one(tmp_path):
    scope_file = _write(tmp_path, "s.yaml", {"scopes": {"prod": ["db.*"]}})
    deployed = _write(tmp_path, "dep.yaml", {"db": {"host": "old"}, "cache": {"ttl": 60}})
    source = _write(tmp_path, "src.yaml", {"db": {"host": "new"}, "cache": {"ttl": 60}})
    ns = _ns(scope_file=scope_file, scope_name="prod", deployed=deployed, source=source)
    assert _dispatch(ns) == 1


def test_dispatch_drift_outside_scope_returns_zero(tmp_path):
    scope_file = _write(tmp_path, "s.yaml", {"scopes": {"prod": ["db.*"]}})
    deployed = _write(tmp_path, "dep.yaml", {"db": {"host": "same"}, "cache": {"ttl": 30}})
    source = _write(tmp_path, "src.yaml", {"db": {"host": "same"}, "cache": {"ttl": 60}})
    ns = _ns(scope_file=scope_file, scope_name="prod", deployed=deployed, source=source)
    assert _dispatch(ns) == 0

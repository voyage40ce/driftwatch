"""Tests for driftwatch.inspector and driftwatch.commands.inspector_cmd."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest
import yaml

from driftwatch.inspector import (
    InspectorError,
    FieldInfo,
    InspectResult,
    format_inspect,
    inspect_config,
)
from driftwatch.commands.inspector_cmd import _dispatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.dump(data))
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        config="cfg.yaml",
        env="test",
        show_values=False,
        secrets_only=False,
        min_depth=0,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# inspect_config unit tests
# ---------------------------------------------------------------------------

def test_inspect_returns_inspect_result():
    result = inspect_config({"a": 1}, env="prod")
    assert isinstance(result, InspectResult)
    assert result.env == "prod"


def test_inspect_flat_config_total():
    result = inspect_config({"host": "localhost", "port": 8080})
    assert result.total == 2


def test_inspect_nested_config_uses_dot_notation():
    result = inspect_config({"db": {"host": "localhost"}})
    keys = [f.key for f in result.fields]
    assert "db.host" in keys


def test_inspect_detects_secret_field():
    result = inspect_config({"db_password": "s3cr3t"})
    assert result.secret_count == 1
    assert result.fields[0].is_secret


def test_inspect_non_secret_field():
    result = inspect_config({"host": "localhost"})
    assert result.secret_count == 0


def test_inspect_non_dict_raises():
    with pytest.raises(InspectorError):
        inspect_config(["not", "a", "dict"])


def test_inspect_value_type_recorded():
    result = inspect_config({"count": 42})
    assert result.fields[0].value_type == "int"


# ---------------------------------------------------------------------------
# format_inspect tests
# ---------------------------------------------------------------------------

def test_format_inspect_contains_env():
    result = inspect_config({"x": 1}, env="staging")
    out = format_inspect(result)
    assert "staging" in out


def test_format_inspect_show_values_includes_value():
    result = inspect_config({"host": "localhost"})
    out = format_inspect(result, show_values=True)
    assert "localhost" in out


def test_format_inspect_secret_value_hidden_even_with_show_values():
    result = inspect_config({"api_key": "topsecret"})
    out = format_inspect(result, show_values=True)
    assert "topsecret" not in out
    assert "[SECRET]" in out


# ---------------------------------------------------------------------------
# _dispatch (CLI) tests
# ---------------------------------------------------------------------------

def test_dispatch_returns_zero_on_valid_config(tmp_path):
    p = _write(tmp_path, {"host": "localhost", "port": 5432})
    ns = _ns(config=str(p))
    assert _dispatch(ns) == 0


def test_dispatch_missing_file_returns_two(tmp_path):
    ns = _ns(config=str(tmp_path / "missing.yaml"))
    assert _dispatch(ns) == 2


def test_dispatch_secrets_only_filters(tmp_path, capsys):
    p = _write(tmp_path, {"host": "h", "password": "x"})
    ns = _ns(config=str(p), secrets_only=True)
    _dispatch(ns)
    out = capsys.readouterr().out
    assert "password" in out
    assert "host" not in out


def test_dispatch_min_depth_filters(tmp_path, capsys):
    p = _write(tmp_path, {"top": "v", "nested": {"inner": "v2"}})
    ns = _ns(config=str(p), min_depth=2)
    _dispatch(ns)
    out = capsys.readouterr().out
    assert "nested.inner" in out
    assert "top" not in out

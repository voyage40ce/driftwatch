"""Unit tests for driftwatch.loader."""

import textwrap
from pathlib import Path

import pytest

from driftwatch.loader import ConfigLoadError, load_pair, load_yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_yaml(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_yaml
# ---------------------------------------------------------------------------

def test_load_yaml_returns_dict(tmp_path):
    p = write_yaml(tmp_path, "cfg.yaml", """\
        database:
          host: localhost
          port: 5432
    """)
    result = load_yaml(p)
    assert result == {"database": {"host": "localhost", "port": 5432}}


def test_load_yaml_empty_file_returns_empty_dict(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    assert load_yaml(p) == {}


def test_load_yaml_missing_file_raises(tmp_path):
    with pytest.raises(ConfigLoadError, match="File not found"):
        load_yaml(tmp_path / "nonexistent.yaml")


def test_load_yaml_invalid_yaml_raises(tmp_path):
    p = write_yaml(tmp_path, "bad.yaml", "key: [unclosed")
    with pytest.raises(ConfigLoadError, match="Invalid YAML"):
        load_yaml(p)


def test_load_yaml_non_mapping_raises(tmp_path):
    p = write_yaml(tmp_path, "list.yaml", "- item1\n- item2\n")
    with pytest.raises(ConfigLoadError, match="Expected a YAML mapping"):
        load_yaml(p)


# ---------------------------------------------------------------------------
# load_pair
# ---------------------------------------------------------------------------

def test_load_pair_returns_both(tmp_path):
    sot = write_yaml(tmp_path, "sot.yaml", "app: myapp\n")
    dep = write_yaml(tmp_path, "dep.yaml", "app: myapp\nenv: prod\n")
    expected, actual = load_pair(sot, dep)
    assert expected == {"app": "myapp"}
    assert actual == {"app": "myapp", "env": "prod"}

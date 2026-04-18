"""Tests for driftwatch.templater."""
from __future__ import annotations

import pytest
import yaml

from driftwatch.templater import (
    RenderResult,
    TemplaterError,
    load_template,
    render_template,
)


def _write(tmp_path, data):
    p = tmp_path / "tmpl.yaml"
    p.write_text(yaml.dump(data))
    return str(p)


def test_render_no_variables_unchanged():
    tmpl = {"host": "localhost", "port": 8080}
    result = render_template(tmpl, {})
    assert result.rendered == tmpl
    assert result.substitutions == {}
    assert result.unresolved == []


def test_render_substitutes_variable():
    tmpl = {"host": "{{ HOST }}"}
    result = render_template(tmpl, {"HOST": "prod.example.com"})
    assert result.rendered["host"] == "prod.example.com"
    assert result.substitutions["HOST"] == "prod.example.com"


def test_render_unresolved_variable_kept_as_is():
    tmpl = {"host": "{{ MISSING }}"}
    result = render_template(tmpl, {})
    assert result.rendered["host"] == "{{ MISSING }}"
    assert "MISSING" in result.unresolved


def test_render_nested_dict():
    tmpl = {"db": {"url": "{{ DB_URL }}"}}
    result = render_template(tmpl, {"DB_URL": "postgres://localhost/db"})
    assert result.rendered["db"]["url"] == "postgres://localhost/db"


def test_render_list_values():
    tmpl = {"hosts": ["{{ H1 }}", "{{ H2 }}"]}
    result = render_template(tmpl, {"H1": "a", "H2": "b"})
    assert result.rendered["hosts"] == ["a", "b"]


def test_render_partial_substitution_in_string():
    tmpl = {"dsn": "postgres://{{ USER }}:{{ PASS }}@localhost"}
    result = render_template(tmpl, {"USER": "admin", "PASS": "secret"})
    assert result.rendered["dsn"] == "postgres://admin:secret@localhost"


def test_load_template_returns_dict(tmp_path):
    p = _write(tmp_path, {"key": "{{ VAL }}"})
    data = load_template(p)
    assert isinstance(data, dict)
    assert "key" in data


def test_load_template_missing_file_raises(tmp_path):
    with pytest.raises(TemplaterError, match="not found"):
        load_template(str(tmp_path / "nope.yaml"))


def test_load_template_invalid_yaml_raises(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(": : :")
    with pytest.raises(TemplaterError, match="Invalid YAML"):
        load_template(str(p))


def test_load_template_non_mapping_raises(tmp_path):
    p = tmp_path / "list.yaml"
    p.write_text("- a\n- b\n")
    with pytest.raises(TemplaterError, match="mapping"):
        load_template(str(p))

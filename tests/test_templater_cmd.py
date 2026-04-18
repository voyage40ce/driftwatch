"""Tests for driftwatch.commands.templater_cmd."""
from __future__ import annotations

import argparse

import pytest
import yaml

from driftwatch.commands.templater_cmd import _dispatch


def _write(tmp_path, data):
    p = tmp_path / "tmpl.yaml"
    p.write_text(yaml.dump(data))
    return str(p)


def _ns(**kwargs):
    defaults = dict(template="", vars=[], out=None, strict=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_dispatch_no_vars_returns_zero(tmp_path, capsys):
    p = _write(tmp_path, {"host": "localhost"})
    rc = _dispatch(_ns(template=p))
    assert rc == 0
    out = capsys.readouterr().out
    assert "localhost" in out


def test_dispatch_with_var_substitutes(tmp_path, capsys):
    p = _write(tmp_path, {"host": "{{ HOST }}"})
    rc = _dispatch(_ns(template=p, vars=["HOST=myhost"]))
    assert rc == 0
    assert "myhost" in capsys.readouterr().out


def test_dispatch_unresolved_warns(tmp_path, capsys):
    p = _write(tmp_path, {"host": "{{ MISSING }}"})
    rc = _dispatch(_ns(template=p))
    assert rc == 0
    assert "MISSING" in capsys.readouterr().err


def test_dispatch_strict_unresolved_returns_two(tmp_path):
    p = _write(tmp_path, {"host": "{{ MISSING }}"})
    rc = _dispatch(_ns(template=p, strict=True))
    assert rc == 2


def test_dispatch_missing_file_returns_two(tmp_path):
    rc = _dispatch(_ns(template=str(tmp_path / "nope.yaml")))
    assert rc == 2


def test_dispatch_invalid_var_format_returns_two(tmp_path):
    p = _write(tmp_path, {"x": "1"})
    rc = _dispatch(_ns(template=p, vars=["BADFORMAT"]))
    assert rc == 2


def test_dispatch_writes_to_out_file(tmp_path):
    p = _write(tmp_path, {"key": "{{ VAL }}"})
    out = str(tmp_path / "out.yaml")
    rc = _dispatch(_ns(template=p, vars=["VAL=hello"], out=out))
    assert rc == 0
    content = (tmp_path / "out.yaml").read_text()
    assert "hello" in content

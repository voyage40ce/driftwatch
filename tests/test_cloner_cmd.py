"""Tests for driftwatch.commands.cloner_cmd."""
import argparse
import yaml
import pytest

from driftwatch.commands.cloner_cmd import _dispatch, _parse_overrides, register


SOURCE = {"db": {"host": "prod-db", "port": 5432}, "debug": False}


def _write(tmp_path, data):
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.dump(data))
    return str(p)


def _ns(source_file, source_env="prod", target_env="staging", overrides=None, out=None):
    ns = argparse.Namespace(
        source_file=source_file,
        source_env=source_env,
        target_env=target_env,
        overrides=overrides or [],
        out=out,
    )
    return ns


def test_dispatch_returns_zero_on_success(tmp_path, capsys):
    p = _write(tmp_path, SOURCE)
    code = _dispatch(_ns(p))
    assert code == 0


def test_dispatch_outputs_yaml(tmp_path, capsys):
    p = _write(tmp_path, SOURCE)
    _dispatch(_ns(p))
    out = capsys.readouterr().out
    parsed = yaml.safe_load(out)
    assert parsed["db"]["host"] == "prod-db"


def test_dispatch_applies_override(tmp_path, capsys):
    p = _write(tmp_path, SOURCE)
    code = _dispatch(_ns(p, overrides=["db.host=staging-db"]))
    assert code == 0
    out = capsys.readouterr().out
    parsed = yaml.safe_load(out)
    assert parsed["db"]["host"] == "staging-db"


def test_dispatch_writes_out_file(tmp_path, capsys):
    p = _write(tmp_path, SOURCE)
    out_file = str(tmp_path / "out.yaml")
    code = _dispatch(_ns(p, out=out_file))
    assert code == 0
    with open(out_file) as fh:
        parsed = yaml.safe_load(fh)
    assert parsed["db"]["port"] == 5432


def test_dispatch_missing_file_returns_two(tmp_path):
    code = _dispatch(_ns(str(tmp_path / "missing.yaml")))
    assert code == 2


def test_dispatch_bad_override_returns_two(tmp_path):
    p = _write(tmp_path, SOURCE)
    code = _dispatch(_ns(p, overrides=["no-equals-sign"]))
    assert code == 2


def test_parse_overrides_empty():
    assert _parse_overrides([]) == {}


def test_parse_overrides_single():
    assert _parse_overrides(["key=val"]) == {"key": "val"}


def test_parse_overrides_bad_raises():
    with pytest.raises(ValueError):
        _parse_overrides(["badvalue"])

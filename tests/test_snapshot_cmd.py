"""Tests for driftwatch/commands/snapshot_cmd.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
import yaml

from driftwatch.commands.snapshot_cmd import _cmd_save, _cmd_diff, _cmd_list


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data))


def _write_snapshot(snap_dir: Path, name: str, config: dict,
                    saved_at: str = "2024-01-01T00:00:00") -> None:
    snap_dir.mkdir(parents=True, exist_ok=True)
    payload = {"name": name, "saved_at": saved_at, "source": "test.yaml", "config": config}
    (snap_dir / f"{name}.json").write_text(json.dumps(payload))


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"snap_dir": None, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _cmd_save
# ---------------------------------------------------------------------------

def test_cmd_save_creates_snapshot(tmp_path):
    cfg = tmp_path / "app.yaml"
    _write_yaml(cfg, {"host": "localhost"})
    snap_dir = str(tmp_path / "snaps")
    args = _ns(name="v1", config=str(cfg), snap_dir=snap_dir)
    rc = _cmd_save(args)
    assert rc == 0
    assert (tmp_path / "snaps" / "v1.json").exists()


def test_cmd_save_missing_config_returns_two(tmp_path):
    args = _ns(name="v1", config=str(tmp_path / "missing.yaml"),
               snap_dir=str(tmp_path / "snaps"))
    rc = _cmd_save(args)
    assert rc == 2


# ---------------------------------------------------------------------------
# _cmd_diff
# ---------------------------------------------------------------------------

def test_cmd_diff_no_drift_returns_zero(tmp_path):
    config = {"host": "prod", "port": 8080}
    snap_dir = tmp_path / "snaps"
    _write_snapshot(snap_dir, "v1", config)
    cfg_file = tmp_path / "app.yaml"
    _write_yaml(cfg_file, config)
    args = _ns(name="v1", config=str(cfg_file), snap_dir=str(snap_dir))
    rc = _cmd_diff(args)
    assert rc == 0


def test_cmd_diff_drift_returns_one(tmp_path):
    snap_dir = tmp_path / "snaps"
    _write_snapshot(snap_dir, "v1", {"host": "prod"})
    cfg_file = tmp_path / "app.yaml"
    _write_yaml(cfg_file, {"host": "staging"})
    args = _ns(name="v1", config=str(cfg_file), snap_dir=str(snap_dir))
    rc = _cmd_diff(args)
    assert rc == 1


def test_cmd_diff_missing_snapshot_returns_two(tmp_path):
    cfg_file = tmp_path / "app.yaml"
    _write_yaml(cfg_file, {})
    args = _ns(name="ghost", config=str(cfg_file), snap_dir=str(tmp_path / "snaps"))
    rc = _cmd_diff(args)
    assert rc == 2


# ---------------------------------------------------------------------------
# _cmd_list
# ---------------------------------------------------------------------------

def test_cmd_list_empty_dir(tmp_path, capsys):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    args = _ns(snap_dir=str(snap_dir))
    rc = _cmd_list(args)
    assert rc == 0
    assert "No snapshots" in capsys.readouterr().out


def test_cmd_list_shows_snapshots(tmp_path, capsys):
    snap_dir = tmp_path / "snaps"
    _write_snapshot(snap_dir, "v1", {})
    _write_snapshot(snap_dir, "v2", {})
    args = _ns(snap_dir=str(snap_dir))
    rc = _cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "v1" in out
    assert "v2" in out

"""Tests for driftwatch.pinner and commands.pinner_cmd."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from driftwatch.pinner import PinnerError, delete_pin, list_pins, load_pin, pin_config
from driftwatch.commands.pinner_cmd import _dispatch


@pytest.fixture()
def pins_dir(tmp_path: Path) -> Path:
    return tmp_path / "pins"


def test_pin_config_creates_file(pins_dir: Path) -> None:
    pin_config("prod", {"key": "val"}, pins_dir=pins_dir)
    assert (pins_dir / "prod.json").exists()


def test_pin_config_stores_config(pins_dir: Path) -> None:
    pin_config("prod", {"a": 1}, pins_dir=pins_dir)
    data = json.loads((pins_dir / "prod.json").read_text())
    assert data["config"] == {"a": 1}


def test_pin_config_stores_note(pins_dir: Path) -> None:
    pin_config("staging", {}, note="initial", pins_dir=pins_dir)
    data = json.loads((pins_dir / "staging.json").read_text())
    assert data["note"] == "initial"


def test_load_pin_returns_entry(pins_dir: Path) -> None:
    pin_config("dev", {"x": 2}, pins_dir=pins_dir)
    entry = load_pin("dev", pins_dir=pins_dir)
    assert entry.env == "dev"
    assert entry.config == {"x": 2}


def test_load_pin_missing_raises(pins_dir: Path) -> None:
    with pytest.raises(PinnerError):
        load_pin("ghost", pins_dir=pins_dir)


def test_list_pins_empty(pins_dir: Path) -> None:
    assert list_pins(pins_dir=pins_dir) == []


def test_list_pins_returns_envs(pins_dir: Path) -> None:
    pin_config("a", {}, pins_dir=pins_dir)
    pin_config("b", {}, pins_dir=pins_dir)
    assert list_pins(pins_dir=pins_dir) == ["a", "b"]


def test_delete_pin_removes_file(pins_dir: Path) -> None:
    pin_config("prod", {}, pins_dir=pins_dir)
    assert delete_pin("prod", pins_dir=pins_dir) is True
    assert not (pins_dir / "prod.json").exists()


def test_delete_pin_missing_returns_false(pins_dir: Path) -> None:
    assert delete_pin("none", pins_dir=pins_dir) is False


# --- CLI dispatch ---

def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"pin_cmd": "list"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_list_returns_zero(capsys) -> None:
    assert _dispatch(_ns(pin_cmd="list")) == 0


def test_cmd_save_missing_file_returns_two(tmp_path: Path) -> None:
    ns = _ns(pin_cmd="save", env="prod", config_file=str(tmp_path / "nope.yaml"), note="")
    assert _dispatch(ns) == 2


def test_cmd_delete_missing_returns_two() -> None:
    ns = _ns(pin_cmd="delete", env="__nonexistent__")
    assert _dispatch(ns) == 2

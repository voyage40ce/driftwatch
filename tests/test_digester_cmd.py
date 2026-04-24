"""Tests for driftwatch.commands.digester_cmd."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import yaml

from driftwatch.commands.digester_cmd import _dispatch
from driftwatch.digester import compute_digest, save_digest


def _write(tmp_path: Path, name: str, data: dict) -> str:
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(digest_cmd=None, env="prod", store=".dw_test/digests")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# compute sub-command
# ---------------------------------------------------------------------------

def test_compute_match_returns_zero(tmp_path: Path):
    src = _write(tmp_path, "src.yaml", {"a": 1})
    live = _write(tmp_path, "live.yaml", {"a": 1})
    ns = _ns(digest_cmd="compute", source=src, live=live)
    assert _dispatch(ns) == 0


def test_compute_mismatch_returns_one(tmp_path: Path):
    src = _write(tmp_path, "src.yaml", {"a": 1})
    live = _write(tmp_path, "live.yaml", {"a": 99})
    ns = _ns(digest_cmd="compute", source=src, live=live)
    assert _dispatch(ns) == 1


def test_compute_missing_file_returns_two(tmp_path: Path):
    ns = _ns(digest_cmd="compute", source="no.yaml", live="no2.yaml")
    assert _dispatch(ns) == 2


# ---------------------------------------------------------------------------
# save sub-command
# ---------------------------------------------------------------------------

def test_save_returns_zero(tmp_path: Path):
    cfg = _write(tmp_path, "cfg.yaml", {"x": 1})
    store = str(tmp_path / "store")
    ns = _ns(digest_cmd="save", config=cfg, store=store)
    assert _dispatch(ns) == 0


def test_save_creates_file(tmp_path: Path):
    cfg = _write(tmp_path, "cfg.yaml", {"x": 1})
    store = tmp_path / "store"
    ns = _ns(digest_cmd="save", config=cfg, store=str(store))
    _dispatch(ns)
    assert (store / "prod.digest.json").exists()


def test_save_missing_config_returns_two(tmp_path: Path):
    ns = _ns(digest_cmd="save", config="missing.yaml", store=str(tmp_path))
    assert _dispatch(ns) == 2


# ---------------------------------------------------------------------------
# compare sub-command
# ---------------------------------------------------------------------------

def test_compare_match_returns_zero(tmp_path: Path):
    cfg = {"a": 1}
    cfg_path = _write(tmp_path, "cfg.yaml", cfg)
    store = tmp_path / "store"
    digest = compute_digest("prod", cfg)
    save_digest(digest, store)
    ns = _ns(digest_cmd="compare", config=cfg_path, store=str(store))
    assert _dispatch(ns) == 0


def test_compare_mismatch_returns_one(tmp_path: Path):
    old_cfg = {"a": 1}
    new_cfg = {"a": 99}
    cfg_path = _write(tmp_path, "cfg.yaml", new_cfg)
    store = tmp_path / "store"
    digest = compute_digest("prod", old_cfg)
    save_digest(digest, store)
    ns = _ns(digest_cmd="compare", config=cfg_path, store=str(store))
    assert _dispatch(ns) == 1


def test_compare_missing_saved_digest_returns_two(tmp_path: Path):
    cfg_path = _write(tmp_path, "cfg.yaml", {"a": 1})
    store = tmp_path / "empty_store"
    ns = _ns(digest_cmd="compare", config=cfg_path, store=str(store))
    assert _dispatch(ns) == 2


def test_dispatch_unknown_cmd_returns_one(tmp_path: Path):
    ns = _ns(digest_cmd="unknown")
    assert _dispatch(ns) == 1

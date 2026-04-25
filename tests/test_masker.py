"""Tests for driftwatch.masker."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import yaml

from driftwatch.masker import (
    MaskOptions,
    MaskerError,
    format_mask_summary,
    mask_config,
)


# ---------------------------------------------------------------------------
# mask_config
# ---------------------------------------------------------------------------

def test_mask_config_leaves_safe_keys_unchanged():
    cfg = {"host": "localhost", "port": 5432}
    result = mask_config(cfg)
    assert result.config == {"host": "localhost", "port": 5432}
    assert result.mask_count == 0


def test_mask_config_masks_password():
    cfg = {"db_password": "s3cr3t", "host": "localhost"}
    result = mask_config(cfg)
    assert result.config["db_password"] == "***"
    assert result.config["host"] == "localhost"
    assert "db_password" in result.masked_keys


def test_mask_config_masks_token_case_insensitive():
    cfg = {"API_TOKEN": "abc123"}
    result = mask_config(cfg)
    assert result.config["API_TOKEN"] == "***"


def test_mask_config_custom_placeholder():
    cfg = {"secret": "mysecret"}
    opts = MaskOptions(placeholder="<REDACTED>")
    result = mask_config(cfg, opts)
    assert result.config["secret"] == "<REDACTED>"


def test_mask_config_nested_key():
    cfg = {"database": {"password": "hunter2", "host": "db"}}
    result = mask_config(cfg)
    assert result.config["database"]["password"] == "***"
    assert result.config["database"]["host"] == "db"
    assert "database.password" in result.masked_keys


def test_mask_config_non_dict_raises():
    with pytest.raises(MaskerError, match="expects a dict"):
        mask_config(["not", "a", "dict"])  # type: ignore[arg-type]


def test_mask_config_invalid_pattern_raises():
    opts = MaskOptions(patterns=["[invalid"])
    with pytest.raises(MaskerError, match="Invalid mask pattern"):
        mask_config({"key": "value"}, opts)


def test_mask_config_case_sensitive_does_not_match_uppercase():
    cfg = {"PASSWORD": "secret"}
    opts = MaskOptions(patterns=[r"password"], case_sensitive=True)
    result = mask_config(cfg, opts)
    # Should NOT be masked because case-sensitive and key is uppercase
    assert result.config["PASSWORD"] == "secret"
    assert result.mask_count == 0


def test_mask_config_additional_pattern():
    cfg = {"internal_key": "value", "safe": "ok"}
    opts = MaskOptions(patterns=[r"internal"])
    result = mask_config(cfg, opts)
    assert result.config["internal_key"] == "***"
    assert result.config["safe"] == "ok"


# ---------------------------------------------------------------------------
# format_mask_summary
# ---------------------------------------------------------------------------

def test_format_mask_summary_no_masks():
    cfg = {"host": "localhost"}
    result = mask_config(cfg)
    summary = format_mask_summary(result)
    assert "No sensitive" in summary


def test_format_mask_summary_lists_keys():
    cfg = {"password": "x", "token": "y"}
    result = mask_config(cfg)
    summary = format_mask_summary(result)
    assert "password" in summary
    assert "token" in summary
    assert "2" in summary


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.dump(data))
    return p


def _ns(config: str, **kwargs) -> argparse.Namespace:
    defaults = {
        "config": config,
        "placeholder": "***",
        "patterns": None,
        "case_sensitive": False,
        "summary": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_dispatch_safe_config_returns_zero(tmp_path):
    from driftwatch.commands.masker_cmd import _dispatch
    p = _write(tmp_path, {"host": "localhost"})
    assert _dispatch(_ns(str(p))) == 0


def test_dispatch_missing_file_returns_two(tmp_path):
    from driftwatch.commands.masker_cmd import _dispatch
    assert _dispatch(_ns(str(tmp_path / "missing.yaml"))) == 2


def test_dispatch_summary_flag(tmp_path, capsys):
    from driftwatch.commands.masker_cmd import _dispatch
    p = _write(tmp_path, {"api_key": "secret", "host": "h"})
    rc = _dispatch(_ns(str(p), summary=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "api_key" in out

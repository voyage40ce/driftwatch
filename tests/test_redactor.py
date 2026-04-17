"""Tests for driftwatch.redactor."""
import pytest
from driftwatch.redactor import (
    RedactOptions,
    RedactorError,
    REDACTED,
    redact_dict,
    redact_flat,
)


def test_redact_dict_leaves_safe_keys_unchanged():
    data = {"host": "localhost", "port": 5432}
    assert redact_dict(data) == data


def test_redact_dict_masks_password():
    data = {"username": "admin", "password": "s3cr3t"}
    result = redact_dict(data)
    assert result["password"] == REDACTED
    assert result["username"] == "admin"


def test_redact_dict_masks_token_case_insensitive():
    data = {"AUTH_TOKEN": "abc123"}
    result = redact_dict(data)
    assert result["AUTH_TOKEN"] == REDACTED


def test_redact_dict_nested():
    data = {"db": {"host": "localhost", "secret": "xyz"}}
    result = redact_dict(data)
    assert result["db"]["secret"] == REDACTED
    assert result["db"]["host"] == "localhost"


def test_redact_dict_custom_placeholder():
    opts = RedactOptions(placeholder="<hidden>")
    data = {"api_key": "key-123"}
    result = redact_dict(data, opts)
    assert result["api_key"] == "<hidden>"


def test_redact_dict_custom_pattern():
    opts = RedactOptions(patterns=[r"^pin$"])
    data = {"pin": "1234", "password": "open"}
    result = redact_dict(data, opts)
    assert result["pin"] == REDACTED
    # password not in custom patterns
    assert result["password"] == "open"


def test_redact_dict_invalid_pattern_raises():
    opts = RedactOptions(patterns=[r"[invalid"])
    with pytest.raises(RedactorError):
        redact_dict({"key": "val"}, opts)


def test_redact_flat_masks_dotted_key():
    flat = {"db.password": "secret", "db.host": "localhost"}
    result = redact_flat(flat)
    assert result["db.password"] == REDACTED
    assert result["db.host"] == "localhost"


def test_redact_flat_safe_keys_unchanged():
    flat = {"app.name": "driftwatch", "app.version": "1.0"}
    assert redact_flat(flat) == flat


def test_redact_dict_does_not_mutate_original():
    data = {"password": "secret"}
    redact_dict(data)
    assert data["password"] == "secret"

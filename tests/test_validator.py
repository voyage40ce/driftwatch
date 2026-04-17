"""Tests for driftwatch.validator."""
import pytest
import yaml
from pathlib import Path

from driftwatch.validator import (
    ValidatorError,
    ValidationResult,
    load_schema,
    validate,
    format_validation_result,
)


def _write(tmp_path: Path, data: dict, name: str = "schema.yaml") -> str:
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return str(p)


def test_load_schema_missing_file_raises(tmp_path):
    with pytest.raises(ValidatorError):
        load_schema(str(tmp_path / "nope.yaml"))


def test_load_schema_missing_fields_key_raises(tmp_path):
    p = _write(tmp_path, {"other": 1})
    with pytest.raises(ValidatorError, match="'fields'"):
        load_schema(p)


def test_load_schema_returns_dict(tmp_path):
    schema = {"fields": {"host": {"required": True, "type": "str"}}}
    p = _write(tmp_path, schema)
    result = load_schema(p)
    assert "fields" in result


def test_validate_passes_when_all_fields_ok():
    schema = {"fields": {"host": {"required": True, "type": "str"}}}
    config = {"host": "localhost"}
    result = validate(config, schema, env="prod")
    assert result.passed
    assert result.env == "prod"


def test_validate_required_field_missing():
    schema = {"fields": {"host": {"required": True}}}
    result = validate({}, schema, env="staging")
    assert not result.passed
    assert any("required" in v for v in result.violations)


def test_validate_wrong_type():
    schema = {"fields": {"port": {"type": "int"}}}
    result = validate({"port": "not-an-int"}, schema)
    assert not result.passed
    assert any("type" in v for v in result.violations)


def test_validate_pattern_mismatch():
    schema = {"fields": {"env": {"pattern": r"(prod|staging|dev)"}}}
    result = validate({"env": "unknown"}, schema)
    assert not result.passed
    assert any("pattern" in v for v in result.violations)


def test_validate_pattern_match():
    schema = {"fields": {"env": {"pattern": r"(prod|staging|dev)"}}}
    result = validate({"env": "prod"}, schema)
    assert result.passed


def test_validate_allowed_values_violation():
    schema = {"fields": {"level": {"allowed": ["low", "medium", "high"]}}}
    result = validate({"level": "critical"}, schema)
    assert not result.passed


def test_validate_allowed_values_ok():
    schema = {"fields": {"level": {"allowed": ["low", "medium", "high"]}}}
    result = validate({"level": "low"}, schema)
    assert result.passed


def test_format_validation_result_passed():
    r = ValidationResult(env="prod")
    out = format_validation_result(r)
    assert "passed" in out
    assert "prod" in out


def test_format_validation_result_failed():
    r = ValidationResult(env="dev", violations=["host: required field is missing"])
    out = format_validation_result(r)
    assert "failed" in out
    assert "host" in out

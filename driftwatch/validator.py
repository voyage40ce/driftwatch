"""Schema validation for config dicts against a simple rules file."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from driftwatch.loader import load_yaml, ConfigLoadError


class ValidatorError(Exception):
    pass


@dataclass
class ValidationResult:
    env: str
    violations: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


def load_schema(path: str) -> dict:
    try:
        data = load_yaml(path)
    except ConfigLoadError as exc:
        raise ValidatorError(str(exc)) from exc
    if not isinstance(data, dict) or "fields" not in data:
        raise ValidatorError("Schema must be a mapping with a 'fields' key")
    return data


def _check_field(key: str, rules: dict, config: dict) -> list[str]:
    violations: list[str] = []
    value: Any = config.get(key)

    if rules.get("required", False) and key not in config:
        violations.append(f"{key}: required field is missing")
        return violations

    if value is None:
        return violations

    expected_type = rules.get("type")
    if expected_type:
        type_map = {"str": str, "int": int, "float": float, "bool": bool}
        py_type = type_map.get(expected_type)
        if py_type and not isinstance(value, py_type):
            violations.append(f"{key}: expected type {expected_type}, got {type(value).__name__}")

    pattern = rules.get("pattern")
    if pattern and isinstance(value, str):
        if not re.fullmatch(pattern, value):
            violations.append(f"{key}: value {value!r} does not match pattern {pattern!r}")

    allowed = rules.get("allowed")
    if allowed is not None and value not in allowed:
        violations.append(f"{key}: value {value!r} not in allowed list {allowed}")

    return violations


def validate(config: dict, schema: dict, env: str = "unknown") -> ValidationResult:
    result = ValidationResult(env=env)
    for key, rules in schema["fields"].items():
        result.violations.extend(_check_field(key, rules, config))
    return result


def format_validation_result(result: ValidationResult) -> str:
    if result.passed:
        return f"[{result.env}] validation passed"
    lines = [f"[{result.env}] validation failed ({len(result.violations)} violation(s)):"]
    for v in result.violations:
        lines.append(f"  - {v}")
    return "\n".join(lines)

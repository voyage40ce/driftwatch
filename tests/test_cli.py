"""Integration tests for the driftwatch CLI entry point."""

import os
import pytest
import yaml

from driftwatch.cli import main


@pytest.fixture
def yaml_files(tmp_path):
    """Returns a helper that writes YAML files and returns their paths."""
    def _write(name: str, data: dict) -> str:
        path = tmp_path / name
        path.write_text(yaml.dump(data))
        return str(path)
    return _write


def test_cli_no_drift_exits_zero(yaml_files):
    expected = yaml_files("expected.yaml", {"app": {"port": 8080}})
    actual = yaml_files("actual.yaml", {"app": {"port": 8080}})
    result = main([expected, actual, "--no-color"])
    assert result == 0


def test_cli_drift_detected_exits_one(yaml_files):
    expected = yaml_files("expected.yaml", {"app": {"port": 8080}})
    actual = yaml_files("actual.yaml", {"app": {"port": 9090}})
    result = main([expected, actual, "--no-color"])
    assert result == 1


def test_cli_missing_file_exits_two(yaml_files, capsys):
    expected = yaml_files("expected.yaml", {"key": "value"})
    result = main([expected, "/nonexistent/path.yaml", "--no-color"])
    assert result == 2
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_cli_output_contains_drift_info(yaml_files, capsys):
    expected = yaml_files("expected.yaml", {"db": {"host": "localhost"}})
    actual = yaml_files("actual.yaml", {"db": {"host": "prod-db"}})
    main([expected, actual, "--no-color"])
    captured = capsys.readouterr()
    assert "db.host" in captured.out
    assert "DRIFT" in captured.out


def test_cli_no_drift_output_shows_ok(yaml_files, capsys):
    expected = yaml_files("expected.yaml", {"service": "api"})
    actual = yaml_files("actual.yaml", {"service": "api"})
    main([expected, actual, "--no-color"])
    captured = capsys.readouterr()
    assert "OK" in captured.out

"""YAML configuration loader for driftwatch."""

import os
from pathlib import Path
from typing import Any

import yaml


class ConfigLoadError(Exception):
    """Raised when a configuration file cannot be loaded or parsed."""


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML file, returning its contents as a dict.

    Args:
        path: Filesystem path to the YAML file.

    Returns:
        Parsed YAML contents as a dictionary.

    Raises:
        ConfigLoadError: If the file does not exist, is unreadable, or
            contains invalid YAML.
    """
    path = Path(path)

    if not path.exists():
        raise ConfigLoadError(f"File not found: {path}")

    if not os.access(path, os.R_OK):
        raise ConfigLoadError(f"Permission denied: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ConfigLoadError(
            f"Expected a YAML mapping at the top level, got {type(data).__name__}: {path}"
        )

    return data


def load_pair(
    source_of_truth: str | Path,
    deployed: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convenience helper that loads both config files in one call.

    Args:
        source_of_truth: Path to the canonical / expected config YAML.
        deployed:        Path to the live / deployed config YAML.

    Returns:
        A tuple of (source_of_truth_dict, deployed_dict).
    """
    return load_yaml(source_of_truth), load_yaml(deployed)

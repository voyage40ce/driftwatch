"""scoper.py – restrict drift reports to a named subset of keys (a 'scope').

A scope is a named list of key-glob patterns.  Only DriftReport items whose
flattened key matches at least one pattern in the scope are kept.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from driftwatch.differ import DriftReport


class ScopeError(Exception):
    """Raised when a scope definition is invalid or missing."""


@dataclass
class Scope:
    name: str
    patterns: List[str]


@dataclass
class ScopeResult:
    scope: Scope
    report: DriftReport
    total_before: int
    total_after: int

    @property
    def filtered_count(self) -> int:
        return self.total_before - self.total_after


def load_scope(path: str, name: str) -> Scope:
    """Load a named scope from a YAML file.

    Expected format::

        scopes:
          production:
            - "db.*"
            - "cache.*"
          staging:
            - "*"
    """
    p = Path(path)
    if not p.exists():
        raise ScopeError(f"Scope file not found: {path}")
    try:
        data = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ScopeError(f"Invalid YAML in scope file: {exc}") from exc
    if not isinstance(data, dict) or "scopes" not in data:
        raise ScopeError("Scope file must contain a top-level 'scopes' mapping")
    scopes = data["scopes"]
    if name not in scopes:
        raise ScopeError(f"Scope '{name}' not defined in {path}")
    patterns = scopes[name]
    if not isinstance(patterns, list):
        raise ScopeError(f"Scope '{name}' must be a list of patterns")
    return Scope(name=name, patterns=patterns)


def apply_scope(report: DriftReport, scope: Scope) -> ScopeResult:
    """Return a new DriftReport containing only items matching the scope."""
    total_before = len(report.changes)
    kept = [
        item
        for item in report.changes
        if any(fnmatch.fnmatch(item["key"], pat) for pat in scope.patterns)
    ]
    scoped_report = DriftReport(
        env=report.env,
        source=report.source,
        changes=kept,
    )
    return ScopeResult(
        scope=scope,
        report=scoped_report,
        total_before=total_before,
        total_after=len(kept),
    )

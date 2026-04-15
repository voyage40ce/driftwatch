"""Policy engine: load drift-ignore rules and evaluate them against a DriftReport."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from driftwatch.differ import DriftReport


class PolicyError(Exception):
    """Raised when a policy file cannot be loaded or is malformed."""


@dataclass
class PolicyRule:
    """A single ignore rule matching drift keys by glob or regex pattern."""

    pattern: str
    match_type: str = "glob"  # "glob" | "regex"
    reason: Optional[str] = None

    def matches(self, key: str) -> bool:
        if self.match_type == "regex":
            return bool(re.fullmatch(self.pattern, key))
        return fnmatch.fnmatch(key, self.pattern)


@dataclass
class Policy:
    """Collection of ignore rules for a named environment."""

    env: str = "*"
    rules: List[PolicyRule] = field(default_factory=list)


def load_policy(path: str | Path) -> Policy:
    """Load a policy YAML file and return a :class:`Policy`.

    Expected format::

        env: production
        ignore:
          - pattern: "feature_flags.*"
            reason: "managed separately"
          - pattern: "^build\\.id$"
            match_type: regex
    """
    p = Path(path)
    if not p.exists():
        raise PolicyError(f"Policy file not found: {path}")
    try:
        raw = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        raise PolicyError(f"Invalid YAML in policy file: {exc}") from exc

    if not isinstance(raw, dict):
        raise PolicyError("Policy file must be a YAML mapping")

    rules: List[PolicyRule] = []
    for entry in raw.get("ignore", []):
        if isinstance(entry, str):
            rules.append(PolicyRule(pattern=entry))
        elif isinstance(entry, dict):
            rules.append(
                PolicyRule(
                    pattern=entry["pattern"],
                    match_type=entry.get("match_type", "glob"),
                    reason=entry.get("reason"),
                )
            )
        else:
            raise PolicyError(f"Unrecognised ignore entry: {entry!r}")

    return Policy(env=raw.get("env", "*"), rules=rules)


def apply_policy(report: DriftReport, policy: Policy) -> DriftReport:
    """Return a new :class:`DriftReport` with policy-ignored keys removed."""

    def _keep(key: str) -> bool:
        return not any(rule.matches(key) for rule in policy.rules)

    filtered = {k: v for k, v in report.changes.items() if _keep(k)}
    return DriftReport(changes=filtered)

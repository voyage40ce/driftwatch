"""Audit log — records every drift-detection event to a JSONL file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftReport

_DEFAULT_AUDIT_DIR = os.environ.get("DRIFTWATCH_AUDIT_DIR", ".driftwatch/audit")


class AuditError(Exception):
    """Raised when an audit log operation fails."""


@dataclass
class AuditEntry:
    timestamp: str
    source_file: str
    deployed_file: str
    has_drift: bool
    changed: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "source_file": self.source_file,
            "deployed_file": self.deployed_file,
            "has_drift": self.has_drift,
            "changed": self.changed,
            "added": self.added,
            "removed": self.removed,
            "label": self.label,
        }

    @staticmethod
    def from_dict(data: dict) -> "AuditEntry":
        return AuditEntry(
            timestamp=data["timestamp"],
            source_file=data["source_file"],
            deployed_file=data["deployed_file"],
            has_drift=data["has_drift"],
            changed=data.get("changed", []),
            added=data.get("added", []),
            removed=data.get("removed", []),
            label=data.get("label"),
        )


def _audit_path(audit_dir: str) -> Path:
    return Path(audit_dir) / "drift_audit.jsonl"


def record(
    report: DriftReport,
    source_file: str,
    deployed_file: str,
    label: Optional[str] = None,
    audit_dir: str = _DEFAULT_AUDIT_DIR,
) -> AuditEntry:
    """Append a drift event to the audit log and return the entry."""
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_file=source_file,
        deployed_file=deployed_file,
        has_drift=report.has_drift,
        changed=list(report.changed.keys()),
        added=list(report.added.keys()),
        removed=list(report.removed.keys()),
        label=label,
    )
    path = _audit_path(audit_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
    except OSError as exc:
        raise AuditError(f"Failed to write audit log: {exc}") from exc
    return entry


def load_entries(audit_dir: str = _DEFAULT_AUDIT_DIR) -> List[AuditEntry]:
    """Return all audit entries from the log file."""
    path = _audit_path(audit_dir)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(AuditEntry.from_dict(json.loads(line)))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Failed to read audit log: {exc}") from exc
    return entries

"""Tests for driftwatch.streamer and driftwatch.commands.streamer_cmd."""
from __future__ import annotations

import json
import os
import types

import pytest

from driftwatch.differ import DriftReport
from driftwatch.streamer import (
    StreamOptions,
    StreamerError,
    _report_to_record,
    stream_reports,
    stream_to_file,
)
from driftwatch.commands.streamer_cmd import _dispatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_report() -> DriftReport:
    return DriftReport(env="prod", changes=[])


def _drift_report() -> DriftReport:
    Change = types.SimpleNamespace
    c = Change(key="db.host", change_type="changed", old_value="old", new_value="new")
    return DriftReport(env="prod", changes=[c])


def _ns(**kwargs):
    defaults = dict(source="s.yaml", deployed="d.yaml", env="prod", output=None, pretty=False, skip_clean=False)
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# _report_to_record
# ---------------------------------------------------------------------------

def test_report_to_record_clean():
    rec = _report_to_record(_clean_report())
    assert rec["has_drift"] is False
    assert rec["change_count"] == 0
    assert rec["changes"] == []


def test_report_to_record_drift():
    rec = _report_to_record(_drift_report())
    assert rec["has_drift"] is True
    assert rec["change_count"] == 1
    assert rec["changes"][0]["key"] == "db.host"


# ---------------------------------------------------------------------------
# stream_reports
# ---------------------------------------------------------------------------

def test_stream_reports_yields_json_lines(tmp_path):
    import io
    buf = io.StringIO()
    lines = list(stream_reports([_clean_report(), _drift_report()], out=buf))
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must be valid JSON


def test_stream_reports_skip_clean(tmp_path):
    import io
    buf = io.StringIO()
    opts = StreamOptions(include_clean=False)
    lines = list(stream_reports([_clean_report(), _drift_report()], options=opts, out=buf))
    assert len(lines) == 1
    assert json.loads(lines[0])["has_drift"] is True


def test_stream_reports_pretty_is_multiline():
    import io
    buf = io.StringIO()
    opts = StreamOptions(pretty=True)
    lines = list(stream_reports([_drift_report()], options=opts, out=buf))
    assert "\n" in lines[0]


# ---------------------------------------------------------------------------
# stream_to_file
# ---------------------------------------------------------------------------

def test_stream_to_file_creates_file(tmp_path):
    dest = str(tmp_path / "out.ndjson")
    count = stream_to_file([_drift_report()], dest)
    assert count == 1
    assert os.path.exists(dest)


def test_stream_to_file_invalid_path_raises():
    with pytest.raises(StreamerError):
        stream_to_file([_drift_report()], "/no/such/dir/out.ndjson")


# ---------------------------------------------------------------------------
# _dispatch (CLI)
# ---------------------------------------------------------------------------

def test_dispatch_no_drift_returns_zero(tmp_path, monkeypatch):
    src = tmp_path / "s.yaml"
    dep = tmp_path / "d.yaml"
    src.write_text("key: val\n")
    dep.write_text("key: val\n")
    ns = _ns(source=str(src), deployed=str(dep))
    assert _dispatch(ns) == 0


def test_dispatch_drift_returns_one(tmp_path):
    src = tmp_path / "s.yaml"
    dep = tmp_path / "d.yaml"
    src.write_text("key: original\n")
    dep.write_text("key: changed\n")
    ns = _ns(source=str(src), deployed=str(dep))
    assert _dispatch(ns) == 1


def test_dispatch_missing_file_returns_two(tmp_path):
    ns = _ns(source="/no/such/file.yaml", deployed="/no/such/file2.yaml")
    assert _dispatch(ns) == 2


def test_dispatch_writes_output_file(tmp_path):
    src = tmp_path / "s.yaml"
    dep = tmp_path / "d.yaml"
    out = tmp_path / "result.ndjson"
    src.write_text("key: val\n")
    dep.write_text("key: val\n")
    ns = _ns(source=str(src), deployed=str(dep), output=str(out))
    _dispatch(ns)
    assert out.exists()
    data = json.loads(out.read_text().strip())
    assert "has_drift" in data

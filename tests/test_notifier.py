"""Tests for driftwatch.notifier."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from driftwatch.differ import DriftReport
from driftwatch.notifier import (
    NotifyError,
    NotifyOptions,
    _build_payload,
    notify_if_drift,
    send_webhook,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_report() -> DriftReport:
    return DriftReport(changed={}, added={}, removed={})


def _drift_report() -> DriftReport:
    return DriftReport(
        changed={"db.port": (5432, 9999)},
        added={"new.key": "val"},
        removed={"old.key": "gone"},
    )


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------

def test_build_payload_no_drift():
    payload = _build_payload(_clean_report(), "staging")
    assert payload["has_drift"] is False
    assert payload["env"] == "staging"
    assert payload["changed"] == []
    assert payload["added"] == []
    assert payload["removed"] == []


def test_build_payload_with_drift():
    payload = _build_payload(_drift_report(), "prod")
    assert payload["has_drift"] is True
    assert payload["changed"][0]["key"] == "db.port"
    assert payload["changed"][0]["expected"] == 5432
    assert payload["changed"][0]["actual"] == 9999
    assert "new.key" in payload["added"]
    assert "old.key" in payload["removed"]


# ---------------------------------------------------------------------------
# send_webhook
# ---------------------------------------------------------------------------

def test_send_webhook_raises_without_url():
    opts = NotifyOptions(webhook_url=None)
    with pytest.raises(NotifyError, match="webhook_url is required"):
        send_webhook(_drift_report(), opts)


def test_send_webhook_posts_json(tmp_path):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.method
        captured["body"] = json.loads(req.data)
        captured["ct"] = req.get_header("Content-type")
        return MagicMock(__enter__=lambda s: s, __exit__=MagicMock(return_value=False))

    opts = NotifyOptions(webhook_url="http://example.com/hook", env="prod")
    with patch("driftwatch.notifier.urllib.request.urlopen", side_effect=fake_urlopen):
        send_webhook(_drift_report(), opts)

    assert captured["url"] == "http://example.com/hook"
    assert captured["method"] == "POST"
    assert captured["ct"] == "application/json"
    assert captured["body"]["env"] == "prod"


def test_send_webhook_raises_on_url_error():
    opts = NotifyOptions(webhook_url="http://bad.host/hook")
    err = urllib.error.URLError("connection refused")
    with patch("driftwatch.notifier.urllib.request.urlopen", side_effect=err):
        with pytest.raises(NotifyError, match="Webhook delivery failed"):
            send_webhook(_drift_report(), opts)


# ---------------------------------------------------------------------------
# notify_if_drift
# ---------------------------------------------------------------------------

def test_notify_if_drift_skips_when_no_drift():
    sender = MagicMock()
    result = notify_if_drift(_clean_report(), NotifyOptions(), sender=sender)
    assert result is False
    sender.assert_not_called()


def test_notify_if_drift_sends_when_drift():
    sender = MagicMock()
    opts = NotifyOptions(webhook_url="http://example.com/hook", env="prod")
    result = notify_if_drift(_drift_report(), opts, sender=sender)
    assert result is True
    sender.assert_called_once()

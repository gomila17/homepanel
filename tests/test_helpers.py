"""Unit tests for the small pure-logic helpers that get touched most often
while iterating on panels: label formatting and the LAN/domain name-and-kind
inheritance. These don't need a running server or any configured integration.
"""

from datetime import datetime, timedelta, timezone

from app.integrations import n8n
from app.integrations.apps import _inherit_from_apps
from app.main import _infra_service


# --- n8n._when_label / _duration_label -------------------------------------


def test_when_label_no_timestamp():
    assert n8n._when_label(None) == "—"


def test_when_label_minutes():
    started = datetime.now(timezone.utc) - timedelta(minutes=8)
    assert n8n._when_label(started) == "-8M"


def test_when_label_hours():
    started = datetime.now(timezone.utc) - timedelta(hours=3)
    assert n8n._when_label(started) == "-3H"


def test_when_label_days():
    started = datetime.now(timezone.utc) - timedelta(days=2, hours=1)
    assert n8n._when_label(started) == "-2D"


def test_duration_label_missing_timestamps():
    assert n8n._duration_label(None, None) == "—"


def test_duration_label_seconds():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    stop = start + timedelta(seconds=1.2)
    assert n8n._duration_label(start, stop) == "1.2s"


def test_duration_label_minutes():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    stop = start + timedelta(minutes=2, seconds=30)
    assert n8n._duration_label(start, stop) == "2.5m"


# --- apps._inherit_from_apps -------------------------------------------------


def test_inherit_from_apps_matches_by_name_case_insensitive(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.apps.config.APPS",
        [{"name": "Vikunja", "kind": "TASK MANAGER", "url": "https://tasks.example.com"}],
    )
    result = _inherit_from_apps({"name": "vikunja", "url": "http://192.0.2.10:8082"})
    assert result["name"] == "Vikunja"
    assert result["kind"] == "TASK MANAGER"
    assert result["url"] == "http://192.0.2.10:8082"


def test_inherit_from_apps_keeps_own_kind_when_no_match(monkeypatch):
    monkeypatch.setattr("app.integrations.apps.config.APPS", [])
    result = _inherit_from_apps(
        {"name": "Uptime Kuma", "kind": "MONITORING", "url": "http://192.0.2.11:3001"}
    )
    assert result["name"] == "Uptime Kuma"
    assert result["kind"] == "MONITORING"


def test_inherit_from_apps_entry_kind_wins_over_matched_kind(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.apps.config.APPS",
        [{"name": "n8n", "kind": "WORKFLOW AUTOMATION", "url": "https://n8n.example.com"}],
    )
    result = _inherit_from_apps({"name": "n8n", "kind": "OVERRIDE", "url": "http://192.0.2.12"})
    assert result["kind"] == "OVERRIDE"


# --- main._infra_service -----------------------------------------------------


def test_infra_service_not_configured():
    service = _infra_service("N8N", "", configured=False, reachable=False, meta=None)
    assert service["state"] == "SIN CONFIGURAR"
    assert service["css"] == "dim"
    assert service["url"] == "#"
    assert service["meta"] == "—"


def test_infra_service_configured_and_reachable():
    service = _infra_service(
        "VIKUNJA", "https://tasks.example.com", configured=True, reachable=True, meta="3 TAREAS"
    )
    assert service["state"] == "ONLINE"
    assert service["css"] == "ok"
    assert service["meta"] == "3 TAREAS"


def test_infra_service_configured_but_unreachable():
    service = _infra_service(
        "PROXMOX VE", "https://pve.example.com", configured=True, reachable=False, meta=None
    )
    assert service["state"] == "SIN RESPUESTA"
    assert service["css"] == "error"

"""Regression tests for a real production bug: a configured integration whose
target responds 200 with an empty/non-JSON body (bad credentials, wrong URL,
a login page instead of the API...) crashed with an uncaught
json.JSONDecodeError instead of falling back to "no data", because every
integration only caught httpx.HTTPError around its response.json() calls —
and JSONDecodeError doesn't inherit from that.

Each test configures the integration (so it doesn't short-circuit on
"not configured"), monkeypatches httpx.AsyncClient's request methods to
return an empty 200 response, and asserts the graceful fallback value
instead of an exception. Plain asyncio.run() rather than pytest-asyncio,
to avoid a new test-only dependency for one file.
"""

import asyncio

import httpx
import pytest

from app import config
from app.integrations import adguard, cloudflare, n8n, npm, proxmox, vikunja, weather


def _empty_ok(method: str, url) -> httpx.Response:
    # A request must be attached, or response.raise_for_status() (which every
    # integration calls before .json()) errors before the bug even triggers.
    return httpx.Response(200, content=b"", request=httpx.Request(method, url))


@pytest.fixture
def empty_response(monkeypatch):
    """Make every AsyncClient.get/post return a 200 with an empty body."""

    async def fake_get(self, url, *a, **kw):
        return _empty_ok("GET", url)

    async def fake_post(self, url, *a, **kw):
        return _empty_ok("POST", url)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)


def test_adguard_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "ADGUARD_BASE_URL", "http://adguard.example.com")
    monkeypatch.setattr(config, "ADGUARD_USERNAME", "user")
    monkeypatch.setattr(config, "ADGUARD_PASSWORD", "pass")
    assert asyncio.run(adguard.get_stats()) == {}


def test_weather_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "OPENWEATHER_API_KEY", "key")
    monkeypatch.setattr(config, "OPENWEATHER_LOCATION", "Sabadell,ES")
    assert asyncio.run(weather.get_current()) is None


def test_n8n_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "N8N_BASE_URL", "http://n8n.example.com")
    monkeypatch.setattr(config, "N8N_API_KEY", "key")
    assert asyncio.run(n8n.get_recent_executions()) == []


def test_vikunja_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "VIKUNJA_BASE_URL", "http://vikunja.example.com")
    monkeypatch.setattr(config, "VIKUNJA_API_TOKEN", "token")
    assert asyncio.run(vikunja.get_open_tasks()) == []


def test_npm_survives_empty_body(monkeypatch, empty_response):
    # NPM authenticates first (POST), then calls two GETs — the empty body
    # hits on the very first (the auth) call.
    monkeypatch.setattr(config, "NPM_BASE_URL", "http://npm.example.com")
    monkeypatch.setattr(config, "NPM_EMAIL", "user@example.com")
    monkeypatch.setattr(config, "NPM_PASSWORD", "pass")
    assert asyncio.run(npm.get_summary()) == {}


def test_cloudflare_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "CLOUDFLARE_API_TOKEN", "token")
    monkeypatch.setattr(config, "CLOUDFLARE_ACCOUNT_ID", "account")
    monkeypatch.setattr(config, "CLOUDFLARE_TUNNEL_ID", "tunnel")
    assert asyncio.run(cloudflare.get_tunnel_status()) == {}


def test_proxmox_status_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "PROXMOX_BASE_URL", "https://pve.example.com:8006")
    monkeypatch.setattr(config, "PROXMOX_TOKEN_ID", "user@pam!token")
    monkeypatch.setattr(config, "PROXMOX_TOKEN_SECRET", "secret")
    assert asyncio.run(proxmox.get_status()) == {"nodes": [], "guests": []}


def test_proxmox_telemetry_survives_empty_body(monkeypatch, empty_response):
    monkeypatch.setattr(config, "PROXMOX_BASE_URL", "https://pve.example.com:8006")
    monkeypatch.setattr(config, "PROXMOX_TOKEN_ID", "user@pam!token")
    monkeypatch.setattr(config, "PROXMOX_TOKEN_SECRET", "secret")
    assert asyncio.run(proxmox.get_telemetry()) == {}

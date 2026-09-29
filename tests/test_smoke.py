"""Route-level smoke tests.

With no .env at all, every integration module short-circuits to its
"not configured" empty state instead of making a real HTTP call, so every
route should still render 200. This is the regression test for the kind of
bug the CI/deploy gate exists to catch: earlier in this project, the index
route 500'd unconditionally (a Jinja `tojson` filter choking on an
undefined template variable) and would have been auto-deployed as-is by
the polling updater, since nothing exercised "/" before it reached main.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/partials/n8n-executions",
        "/partials/vikunja",
        "/partials/applications",
        "/partials/lan-apps",
        "/partials/system-telemetry",
        "/partials/network-security",
        "/partials/infrastructure",
        "/partials/weather",
    ],
)
def test_route_ok_with_no_integrations_configured(path):
    response = client.get(path)
    assert response.status_code == 200

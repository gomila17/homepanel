from datetime import datetime, timezone

import httpx

from app import config


def _configured() -> bool:
    return bool(config.NPM_BASE_URL and config.NPM_EMAIL and config.NPM_PASSWORD)


async def _authenticate(client: httpx.AsyncClient, base: str) -> str:
    response = await client.post(
        f"{base}/api/tokens",
        json={"identity": config.NPM_EMAIL, "secret": config.NPM_PASSWORD},
    )
    response.raise_for_status()
    return response.json().get("token")


async def get_summary() -> dict:
    """Fetch proxy host and SSL certificate counts from Nginx Proxy Manager.

    Returns {} (rather than raising) when NPM isn't configured or
    unreachable, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return {}

    base = config.NPM_BASE_URL.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            token = await _authenticate(client, base)
            headers = {"Authorization": f"Bearer {token}"}

            hosts_response = await client.get(
                f"{base}/api/nginx/proxy-hosts", headers=headers
            )
            hosts_response.raise_for_status()
            hosts = hosts_response.json()

            certs_response = await client.get(
                f"{base}/api/nginx/certificates", headers=headers
            )
            certs_response.raise_for_status()
            certs = certs_response.json()
    except httpx.HTTPError:
        return {}

    return _summarize(hosts, certs)


def _summarize(hosts: list[dict], certs: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    expiries = []
    for cert in certs:
        expires_on = cert.get("expires_on")
        if not expires_on:
            continue
        try:
            expiries.append(datetime.fromisoformat(expires_on.replace("Z", "+00:00")))
        except ValueError:
            continue

    next_expiry_days = max((min(expiries) - now).days, 0) if expiries else None

    return {
        "hosts_total": len(hosts),
        "hosts_online": sum(1 for h in hosts if h.get("enabled")),
        "certs_total": len(certs),
        "next_expiry_days": next_expiry_days,
    }

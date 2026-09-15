import httpx

from app import config


def _configured() -> bool:
    return bool(config.NPM_BASE_URL and config.NPM_EMAIL and config.NPM_PASSWORD)


async def get_proxy_hosts() -> list[dict]:
    """Fetch proxy hosts from Nginx Proxy Manager.

    Returns an empty list (rather than raising) when NPM isn't configured
    or unreachable, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return []

    base = config.NPM_BASE_URL.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            token_response = await client.post(
                f"{base}/api/tokens",
                json={"identity": config.NPM_EMAIL, "secret": config.NPM_PASSWORD},
            )
            token_response.raise_for_status()
            token = token_response.json().get("token")

            hosts_response = await client.get(
                f"{base}/api/nginx/proxy-hosts",
                headers={"Authorization": f"Bearer {token}"},
            )
            hosts_response.raise_for_status()
            raw_hosts = hosts_response.json()
    except httpx.HTTPError:
        return []

    return [_summarize(host) for host in raw_hosts]


def _summarize(host: dict) -> dict:
    return {
        "domain": ", ".join(host.get("domain_names") or []),
        "enabled": bool(host.get("enabled")),
    }

import httpx

from app import config

API_BASE = "https://api.cloudflare.com/client/v4"


def _configured() -> bool:
    return bool(
        config.CLOUDFLARE_API_TOKEN
        and config.CLOUDFLARE_ACCOUNT_ID
        and config.CLOUDFLARE_TUNNEL_ID
    )


def _headers() -> dict:
    return {"Authorization": f"Bearer {config.CLOUDFLARE_API_TOKEN}"}


async def get_tunnel_status() -> dict:
    """Fetch the Cloudflare Tunnel's status, active connections and route count.

    Returns {} (rather than raising) when Cloudflare isn't configured or
    unreachable, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return {}

    account = config.CLOUDFLARE_ACCOUNT_ID
    tunnel = config.CLOUDFLARE_TUNNEL_ID
    headers = _headers()

    try:
        async with httpx.AsyncClient(timeout=5, headers=headers) as client:
            tunnel_response = await client.get(
                f"{API_BASE}/accounts/{account}/cfd_tunnel/{tunnel}"
            )
            tunnel_response.raise_for_status()
            tunnel_data = tunnel_response.json().get("result") or {}

            config_response = await client.get(
                f"{API_BASE}/accounts/{account}/cfd_tunnel/{tunnel}/configurations"
            )
            config_response.raise_for_status()
            ingress = (
                config_response.json().get("result", {}).get("config", {}).get("ingress")
                or []
            )
    except httpx.HTTPError:
        return {}

    return _summarize(tunnel_data, ingress)


def _summarize(tunnel_data: dict, ingress: list) -> dict:
    status = (tunnel_data.get("status") or "unknown").upper()
    return {
        "status": status,
        "healthy": status == "HEALTHY",
        "connections": len(tunnel_data.get("connections") or []),
        "routes": len(ingress),
    }

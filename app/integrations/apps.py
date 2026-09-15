import asyncio
import time

import httpx

from app import config


def _configured() -> bool:
    return bool(config.APPS)


async def _probe(client: httpx.AsyncClient, app: dict) -> dict:
    start = time.monotonic()
    try:
        response = await client.get(app["url"], timeout=5, follow_redirects=True)
        online = response.status_code < 500
        ms = round((time.monotonic() - start) * 1000)
    except httpx.HTTPError:
        online = False
        ms = None
    return {
        "name": app.get("name", ""),
        "kind": app.get("kind", ""),
        "url": app.get("url", "#"),
        "online": online,
        "ms": ms,
    }


async def get_apps() -> list[dict]:
    """Check reachability of each configured app.

    Returns an empty list (rather than raising) when no apps are
    configured, so the dashboard can render a "no data" state.
    """
    if not config.APPS:
        return []

    async with httpx.AsyncClient() as client:
        return list(await asyncio.gather(*(_probe(client, app) for app in config.APPS)))

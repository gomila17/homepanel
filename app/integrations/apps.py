import asyncio
import time

import httpx

from app import config


def _configured() -> bool:
    return bool(config.APPS or config.LAN_APPS)


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


async def _check(entries: list[dict], *, verify: bool = True) -> list[dict]:
    """Probe every entry concurrently.

    Returns an empty list (rather than raising) when there is nothing to
    check, so the dashboard can render a "no data" state.
    """
    if not entries:
        return []

    async with httpx.AsyncClient(verify=verify) as client:
        return list(await asyncio.gather(*(_probe(client, entry) for entry in entries)))


async def get_apps() -> list[dict]:
    """Check reachability of each app exposed through its public domain."""
    return await _check(config.APPS)


def _inherit_from_apps(entry: dict) -> dict:
    """Fill a LAN entry's name/kind from the matching APPS_JSON app, if any.

    Lets LAN_APPS_JSON only carry the IP url for apps that already exist
    by domain, so names and kinds are defined in one place.
    """
    wanted = entry.get("name", "").strip().lower()
    match = next((a for a in config.APPS if a.get("name", "").strip().lower() == wanted), {})
    return {
        **entry,
        "name": match.get("name") or entry.get("name", ""),
        "kind": entry.get("kind") or match.get("kind", ""),
    }


async def get_lan_apps() -> list[dict]:
    """Check reachability of apps exposed by LAN IP (no internet round-trip).

    TLS verification is off: services reached by IP usually present a
    self-signed certificate, which would otherwise show as OFFLINE.
    """
    return await _check([_inherit_from_apps(e) for e in config.LAN_APPS], verify=False)

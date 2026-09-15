import httpx

from app import config


def _configured() -> bool:
    return bool(
        config.ADGUARD_BASE_URL and config.ADGUARD_USERNAME and config.ADGUARD_PASSWORD
    )


async def get_stats() -> dict:
    """Fetch DNS query stats from AdGuard Home.

    Returns {} (rather than raising) when AdGuard isn't configured or
    unreachable, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return {}

    base = config.ADGUARD_BASE_URL.rstrip("/")
    auth = (config.ADGUARD_USERNAME, config.ADGUARD_PASSWORD)

    try:
        async with httpx.AsyncClient(timeout=5, auth=auth) as client:
            response = await client.get(f"{base}/control/stats")
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        return {}

    return _summarize(data)


def _summarize(data: dict) -> dict:
    requests = data.get("num_dns_queries", 0)
    blocked = data.get("num_blocked_filtering", 0)
    block_rate = round(blocked / requests * 100, 1) if requests else 0
    return {
        "requests": requests,
        "blocked": blocked,
        "block_rate": block_rate,
        "avg_latency_ms": round((data.get("avg_processing_time") or 0) * 1000),
        "hourly_bars": _hourly_bars(data.get("dns_queries") or []),
    }


def _hourly_bars(series: list[int]) -> list[dict]:
    peak = max(series) if series else 0
    bars = []
    for i, value in enumerate(series):
        height_pct = round(value / peak * 100) if peak else 0
        hours_ago = len(series) - 1 - i
        label = "AHORA" if hours_ago == 0 else f"-{hours_ago}H"
        bars.append({"height_pct": max(height_pct, 3), "label": f"{label}: {value}"})
    return bars

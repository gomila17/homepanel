import httpx

from app import config


def _configured() -> bool:
    return bool(config.OPENWEATHER_API_KEY and config.OPENWEATHER_LOCATION)


def location_label() -> str:
    """Human-readable label derived from OPENWEATHER_LOCATION, e.g. "CITY · CC"."""
    if not config.OPENWEATHER_LOCATION:
        return ""
    parts = [p.strip() for p in config.OPENWEATHER_LOCATION.split(",") if p.strip()]
    return " · ".join(p.upper() for p in parts)


async def get_current() -> dict | None:
    """Fetch current weather conditions for the configured location.

    Returns None (rather than raising) when not configured or unreachable,
    so the header can render a "no data" state.
    """
    if not _configured():
        return None

    params = {
        "q": config.OPENWEATHER_LOCATION,
        "appid": config.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "es",
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather", params=params
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        return None

    return _summarize(data)


def _summarize(data: dict) -> dict:
    return {
        "location": data.get("name", "").upper() or location_label(),
        "temp": round(data.get("main", {}).get("temp", 0)),
        "condition": data.get("weather", [{}])[0].get("description", "").upper(),
    }

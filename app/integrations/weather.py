import httpx

from app import config


def _configured() -> bool:
    return bool(config.OPENWEATHER_API_KEY and config.OPENWEATHER_LOCATION)


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
        "location": data.get("name", config.OPENWEATHER_LOCATION.split(",")[0]).upper(),
        "temp": round(data.get("main", {}).get("temp", 0)),
        "condition": data.get("weather", [{}])[0].get("description", "").upper(),
    }

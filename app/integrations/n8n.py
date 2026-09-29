from datetime import datetime, timezone

import httpx

from app import config


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _when_label(started: datetime | None) -> str:
    if not started:
        return "—"
    delta = datetime.now(timezone.utc) - started
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"-{max(minutes, 0)}M"
    hours = minutes // 60
    if hours < 24:
        return f"-{hours}H"
    return f"-{hours // 24}D"


def _duration_label(started: datetime | None, stopped: datetime | None) -> str:
    if not started or not stopped:
        return "—"
    seconds = (stopped - started).total_seconds()
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds / 60:.1f}m"


async def get_recent_executions(limit: int = 10) -> list[dict]:
    """Fetch the most recent workflow executions from n8n.

    Returns an empty list (rather than raising) when n8n isn't configured
    or unreachable, so the dashboard can render a "no data" state.
    """
    if not config.N8N_BASE_URL or not config.N8N_API_KEY:
        return []

    url = f"{config.N8N_BASE_URL.rstrip('/')}/api/v1/executions"
    headers = {"X-N8N-API-KEY": config.N8N_API_KEY}
    params = {"limit": limit}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            raw_executions = response.json().get("data", [])
    # ValueError also catches json.JSONDecodeError: a 200 with a non-JSON/empty
    # body (misconfigured credentials, wrong URL...) isn't an httpx.HTTPError.
    except (httpx.HTTPError, ValueError):
        return []

    return [_summarize(execution) for execution in raw_executions]


def _summarize(execution: dict) -> dict:
    has_error = bool(
        execution.get("data", {}).get("resultData", {}).get("error")
    )
    started = _parse_ts(execution.get("startedAt"))
    stopped = _parse_ts(execution.get("stoppedAt"))
    return {
        "workflow_id": execution.get("workflowId"),
        "started_at": execution.get("startedAt"),
        "ok": execution.get("finished", False) and not has_error,
        "when_label": _when_label(started),
        "duration_label": _duration_label(started, stopped),
    }

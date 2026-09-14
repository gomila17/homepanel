import httpx

from app import config


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
    except httpx.HTTPError:
        return []

    return [_summarize(execution) for execution in raw_executions]


def _summarize(execution: dict) -> dict:
    has_error = bool(
        execution.get("data", {}).get("resultData", {}).get("error")
    )
    return {
        "workflow_id": execution.get("workflowId"),
        "started_at": execution.get("startedAt"),
        "ok": execution.get("finished", False) and not has_error,
    }

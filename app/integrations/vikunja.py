from datetime import datetime, timezone

import httpx

from app import config


def _configured() -> bool:
    return bool(config.VIKUNJA_BASE_URL and config.VIKUNJA_API_TOKEN)


def _headers() -> dict:
    return {"Authorization": f"Bearer {config.VIKUNJA_API_TOKEN}"}


def _parse_due(due_date: str | None) -> datetime | None:
    if not due_date or due_date.startswith("0001-"):
        return None
    try:
        return datetime.fromisoformat(due_date.replace("Z", "+00:00"))
    except ValueError:
        return None


def _due_sort_key(task: dict) -> datetime:
    return _parse_due(task.get("due_date")) or datetime.max.replace(tzinfo=timezone.utc)


async def get_open_tasks(limit: int = 10) -> list[dict]:
    """Fetch open (not done) Vikunja tasks, soonest due date first.

    Returns an empty list (rather than raising) when Vikunja isn't
    configured or unreachable, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return []

    base = config.VIKUNJA_BASE_URL.rstrip("/")
    headers = _headers()

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            projects_response = await client.get(f"{base}/api/v1/projects", headers=headers)
            projects_response.raise_for_status()
            # negative ids are Vikunja's pseudo-projects (e.g. "My Open Tasks"),
            # not real projects with their own task lists
            projects = [p for p in projects_response.json() if (p.get("id") or 0) > 0]

            open_tasks = []
            for project in projects:
                tasks_response = await client.get(
                    f"{base}/api/v1/projects/{project['id']}/tasks", headers=headers
                )
                tasks_response.raise_for_status()
                for task in tasks_response.json():
                    if not task.get("done"):
                        open_tasks.append((task, project.get("title", "")))
    except httpx.HTTPError:
        return []

    open_tasks.sort(key=lambda pair: _due_sort_key(pair[0]))

    return [_summarize(task, title) for task, title in open_tasks[:limit]]


def _summarize(task: dict, project_title: str) -> dict:
    due = _parse_due(task.get("due_date"))
    return {
        "title": task.get("title"),
        "project": project_title,
        "due_label": due.strftime("%d/%m %H:%M") if due else "sin fecha",
        "overdue": bool(due and due < datetime.now(timezone.utc)),
    }

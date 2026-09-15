import httpx

from app import config


def _configured() -> bool:
    return bool(
        config.PROXMOX_BASE_URL
        and config.PROXMOX_TOKEN_ID
        and config.PROXMOX_TOKEN_SECRET
    )


def _headers() -> dict:
    return {
        "Authorization": (
            f"PVEAPIToken={config.PROXMOX_TOKEN_ID}={config.PROXMOX_TOKEN_SECRET}"
        )
    }


async def get_status() -> dict:
    """Fetch node and guest (VM/LXC) status from Proxmox.

    Returns {"nodes": [], "guests": []} (rather than raising) when Proxmox
    isn't configured or unreachable, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return {"nodes": [], "guests": []}

    base = config.PROXMOX_BASE_URL.rstrip("/")
    headers = _headers()

    try:
        async with httpx.AsyncClient(
            timeout=5, verify=config.PROXMOX_VERIFY_SSL
        ) as client:
            nodes_response = await client.get(f"{base}/api2/json/nodes", headers=headers)
            nodes_response.raise_for_status()
            raw_nodes = nodes_response.json().get("data", [])

            guests = []
            for node in raw_nodes:
                node_name = node.get("node")
                for kind, resource in (("VM", "qemu"), ("LXC", "lxc")):
                    guests_response = await client.get(
                        f"{base}/api2/json/nodes/{node_name}/{resource}",
                        headers=headers,
                    )
                    guests_response.raise_for_status()
                    for guest in guests_response.json().get("data", []):
                        guests.append(_summarize_guest(guest, kind))
    except httpx.HTTPError:
        return {"nodes": [], "guests": []}

    return {
        "nodes": [_summarize_node(node) for node in raw_nodes],
        "guests": guests,
    }


def _summarize_node(node: dict) -> dict:
    maxmem = node.get("maxmem") or 1
    return {
        "name": node.get("node"),
        "online": node.get("status") == "online",
        "cpu_pct": round((node.get("cpu") or 0) * 100),
        "mem_pct": round((node.get("mem") or 0) / maxmem * 100),
    }


def _summarize_guest(guest: dict, kind: str) -> dict:
    maxmem = guest.get("maxmem") or 1
    return {
        "vmid": guest.get("vmid"),
        "name": guest.get("name"),
        "kind": kind,
        "running": guest.get("status") == "running",
        "mem_pct": round((guest.get("mem") or 0) / maxmem * 100),
    }

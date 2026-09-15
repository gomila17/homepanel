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


async def get_telemetry() -> dict:
    """Fetch host resource usage and a 60-minute history for the first online node.

    Returns {} (rather than raising) when Proxmox isn't configured, unreachable,
    or has no online node, so the dashboard can render a "no data" state.
    """
    if not _configured():
        return {}

    base = config.PROXMOX_BASE_URL.rstrip("/")
    headers = _headers()

    try:
        async with httpx.AsyncClient(
            timeout=5, verify=config.PROXMOX_VERIFY_SSL
        ) as client:
            nodes_response = await client.get(f"{base}/api2/json/nodes", headers=headers)
            nodes_response.raise_for_status()
            raw_nodes = nodes_response.json().get("data", [])
            online_nodes = [n for n in raw_nodes if n.get("status") == "online"]
            if not online_nodes:
                return {}
            node_name = online_nodes[0]["node"]

            status_response = await client.get(
                f"{base}/api2/json/nodes/{node_name}/status", headers=headers
            )
            status_response.raise_for_status()
            status = status_response.json().get("data", {})

            rrd_response = await client.get(
                f"{base}/api2/json/nodes/{node_name}/rrddata",
                headers=headers,
                params={"timeframe": "hour", "cf": "AVERAGE"},
            )
            rrd_response.raise_for_status()
            rrd = rrd_response.json().get("data", [])
    except httpx.HTTPError:
        return {}

    return _summarize_telemetry(node_name, status, rrd)


def _summarize_telemetry(node_name: str, status: dict, rrd: list[dict]) -> dict:
    memory = status.get("memory") or {}
    rootfs = status.get("rootfs") or {}
    loadavg = status.get("loadavg") or ["0"]

    mem_total = memory.get("total") or 1
    root_total = rootfs.get("total") or 1

    cpu_series = [
        round((point.get("cpu") or 0) * 100)
        for point in rrd
        if point.get("cpu") is not None
    ]
    mem_series = [
        round((point.get("memused") or 0) / (point.get("memtotal") or mem_total) * 100)
        for point in rrd
        if point.get("memused") is not None
    ]

    latest = rrd[-1] if rrd else {}
    net_rx_kbs = round((latest.get("netin") or 0) / 1024, 1)
    net_tx_kbs = round((latest.get("netout") or 0) / 1024, 1)

    return {
        "node": node_name,
        "cpu_pct": round((status.get("cpu") or 0) * 100),
        "ram_pct": round((memory.get("used") or 0) / mem_total * 100),
        "storage_pct": round((rootfs.get("used") or 0) / root_total * 100),
        "load_avg": loadavg[0],
        "net_rx_kbs": net_rx_kbs,
        "net_tx_kbs": net_tx_kbs,
        "cpu_points": _svg_points(cpu_series),
        "mem_points": _svg_points(mem_series),
        "cpu_area": _svg_area(cpu_series),
        "peak": max(cpu_series) if cpu_series else 0,
        "avg": round(sum(cpu_series) / len(cpu_series)) if cpu_series else 0,
    }


def _svg_points(series: list[float]) -> str:
    if len(series) < 2:
        return ""
    step = 100 / (len(series) - 1)
    return " ".join(f"{i * step:.2f},{100 - v:.2f}" for i, v in enumerate(series))


def _svg_area(series: list[float]) -> str:
    points = _svg_points(series)
    if not points:
        return ""
    return f"0,100 {points} 100,100"

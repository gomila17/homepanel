import asyncio

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__, config
from app.integrations import adguard, cloudflare, n8n, npm, proxmox, vikunja, weather

app = FastAPI(title="homepanel")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

INTEGRATIONS_CONFIGURED = [
    bool(config.N8N_BASE_URL and config.N8N_API_KEY),
    proxmox._configured(),
    vikunja._configured(),
    adguard._configured(),
    cloudflare._configured(),
    npm._configured(),
]


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": __version__}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "node_name": "HOMELAB-01",
            "services_configured": sum(INTEGRATIONS_CONFIGURED),
            "services_total": len(INTEGRATIONS_CONFIGURED),
            "location_label": weather.location_label(),
            "app_version": __version__,
        },
    )


@app.get("/partials/n8n-executions")
async def n8n_executions(request: Request):
    executions = await n8n.get_recent_executions()
    return templates.TemplateResponse(
        request, "partials/n8n_executions.html", {"executions": executions}
    )


@app.get("/partials/vikunja")
async def vikunja_tasks(request: Request):
    tasks = await vikunja.get_open_tasks()
    return templates.TemplateResponse(request, "partials/vikunja_tasks.html", {"tasks": tasks})


@app.get("/partials/system-telemetry")
async def system_telemetry(request: Request):
    telemetry = await proxmox.get_telemetry()
    return templates.TemplateResponse(
        request, "partials/system_telemetry.html", {"telemetry": telemetry}
    )


@app.get("/partials/network-security")
async def network_security(request: Request):
    tunnel, npm_summary, dns_stats = await asyncio.gather(
        cloudflare.get_tunnel_status(), npm.get_summary(), adguard.get_stats()
    )
    return templates.TemplateResponse(
        request,
        "partials/network_security.html",
        {"tunnel": tunnel, "npm": npm_summary, "dns": dns_stats},
    )


@app.get("/partials/infrastructure")
async def infrastructure(request: Request):
    executions, proxmox_status, tasks, dns_stats, tunnel, npm_summary = await asyncio.gather(
        n8n.get_recent_executions(),
        proxmox.get_status(),
        vikunja.get_open_tasks(),
        adguard.get_stats(),
        cloudflare.get_tunnel_status(),
        npm.get_summary(),
    )

    nodes = proxmox_status.get("nodes", [])
    guests = proxmox_status.get("guests", [])
    tunnel_url = (
        f"https://one.dash.cloudflare.com/{config.CLOUDFLARE_ACCOUNT_ID}/networks/tunnels"
        if config.CLOUDFLARE_ACCOUNT_ID
        else ""
    )

    services = [
        _infra_service(
            "N8N",
            config.N8N_BASE_URL,
            configured=bool(config.N8N_BASE_URL and config.N8N_API_KEY),
            reachable=bool(executions),
            meta=f"{len(executions)} EJECUCIONES" if executions else None,
        ),
        _infra_service(
            "PROXMOX VE",
            config.PROXMOX_BASE_URL,
            configured=proxmox._configured(),
            reachable=any(n["online"] for n in nodes),
            meta=f"{len(guests)} GUESTS" if nodes else None,
        ),
        _infra_service(
            "VIKUNJA",
            config.VIKUNJA_BASE_URL,
            configured=vikunja._configured(),
            reachable=bool(tasks),
            meta=f"{len(tasks)} TAREAS" if tasks else None,
        ),
        _infra_service(
            "ADGUARD HOME",
            config.ADGUARD_BASE_URL,
            configured=adguard._configured(),
            reachable=bool(dns_stats),
            meta=f"{dns_stats['avg_latency_ms']} MS" if dns_stats else None,
        ),
        _infra_service(
            "CLOUDFLARE TUNNEL",
            tunnel_url,
            configured=cloudflare._configured(),
            reachable=bool(tunnel),
            meta=f"{tunnel['routes']} ROUTES" if tunnel else None,
        ),
        _infra_service(
            "NGINX PROXY MANAGER",
            config.NPM_BASE_URL,
            configured=npm._configured(),
            reachable=bool(npm_summary),
            meta=f"{npm_summary['hosts_total']} HOSTS" if npm_summary else None,
        ),
    ]

    return templates.TemplateResponse(
        request,
        "partials/infrastructure.html",
        {"services": services, "guests": guests},
    )


def _infra_service(name: str, url: str, *, configured: bool, reachable: bool, meta: str | None) -> dict:
    if not configured:
        state, css = "SIN CONFIGURAR", "muted"
    elif reachable:
        state, css = "ONLINE", "ok"
    else:
        state, css = "SIN RESPUESTA", "error"
    return {"name": name, "url": url or "#", "state": state, "css": css, "meta": meta or "—"}


@app.get("/partials/weather")
async def weather_status(request: Request):
    current = await weather.get_current()
    return templates.TemplateResponse(
        request,
        "partials/weather.html",
        {"weather": current, "location": weather.location_label()},
    )

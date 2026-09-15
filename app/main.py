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


@app.get("/partials/proxmox")
async def proxmox_status(request: Request):
    status = await proxmox.get_status()
    return templates.TemplateResponse(request, "partials/proxmox_status.html", status)


@app.get("/partials/vikunja")
async def vikunja_tasks(request: Request):
    tasks = await vikunja.get_open_tasks()
    return templates.TemplateResponse(request, "partials/vikunja_tasks.html", {"tasks": tasks})


@app.get("/partials/adguard")
async def adguard_stats(request: Request):
    stats = await adguard.get_stats()
    return templates.TemplateResponse(request, "partials/adguard_stats.html", {"stats": stats})


@app.get("/partials/cloudflare")
async def cloudflare_status(request: Request):
    tunnel = await cloudflare.get_tunnel_status()
    return templates.TemplateResponse(
        request, "partials/cloudflare_status.html", {"tunnel": tunnel}
    )


@app.get("/partials/npm")
async def npm_hosts(request: Request):
    hosts = await npm.get_proxy_hosts()
    return templates.TemplateResponse(request, "partials/npm_hosts.html", {"hosts": hosts})


@app.get("/partials/weather")
async def weather_status(request: Request):
    current = await weather.get_current()
    return templates.TemplateResponse(
        request,
        "partials/weather.html",
        {"weather": current, "location": weather.location_label()},
    )

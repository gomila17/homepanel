from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.integrations import n8n, proxmox, vikunja

app = FastAPI(title="homepanel")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


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

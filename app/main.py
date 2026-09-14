from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.integrations import n8n

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

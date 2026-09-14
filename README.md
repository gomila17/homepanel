# homepanel

Dashboard propio para el homelab, pensado para sustituir a [Homepage](https://github.com/gethomepage/homepage) a medio plazo y como proyecto de portfolio.

## Por qué

Homepage cubre bien la mayoría de apps del homelab, pero no puede:
- Cruzar datos entre apps (p. ej. una línea de tiempo única con caídas de Uptime Kuma + fallos de ejecución de n8n + eventos de Proxmox).
- Integrar con n8n, que no soporta.

## Stack

- **Backend**: Python + [FastAPI](https://fastapi.tiangolo.com/)
- **Frontend**: server-rendered con Jinja2 + [htmx](https://htmx.org/) (sin SPA ni build de JS)

Elegido para minimizar dependencias y footprint, manteniendo el código legible.

## Integraciones (por prioridad)

1. **n8n** — workflows, ejecuciones, éxitos/fallos
2. **Proxmox** — CPU/RAM/VMs/LXC
3. **Vikunja** — tareas/proyectos
4. **Uptime Kuma** — baja prioridad, solo si aporta al cruzar datos
5. **NPM / AdGuard / Cloudflare Tunnel** — paridad con Homepage

Fuera de alcance: Vaultwarden más allá de un simple healthcheck (el cifrado E2E hace inviable extraer datos reales).

## Despliegue

Pensado para un LXC dedicado en Proxmox (no como stack de Portainer en `docker-host`), para que el dashboard no dependa de la misma infraestructura que está monitorizando.

## Desarrollo local

```bash
py -3 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env   # y rellenar credenciales
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Abrir http://127.0.0.1:8000

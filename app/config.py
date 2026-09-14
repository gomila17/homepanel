import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


N8N_BASE_URL = _env("N8N_BASE_URL")
N8N_API_KEY = _env("N8N_API_KEY")

PROXMOX_BASE_URL = _env("PROXMOX_BASE_URL")
PROXMOX_TOKEN_ID = _env("PROXMOX_TOKEN_ID")
PROXMOX_TOKEN_SECRET = _env("PROXMOX_TOKEN_SECRET")

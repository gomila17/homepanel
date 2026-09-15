import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool = True) -> bool:
    return _env(name, str(default)).strip().lower() not in ("false", "0", "no")


N8N_BASE_URL = _env("N8N_BASE_URL")
N8N_API_KEY = _env("N8N_API_KEY")

PROXMOX_BASE_URL = _env("PROXMOX_BASE_URL")
PROXMOX_TOKEN_ID = _env("PROXMOX_TOKEN_ID")
PROXMOX_TOKEN_SECRET = _env("PROXMOX_TOKEN_SECRET")
PROXMOX_VERIFY_SSL = _env_bool("PROXMOX_VERIFY_SSL", True)

VIKUNJA_BASE_URL = _env("VIKUNJA_BASE_URL")
VIKUNJA_API_TOKEN = _env("VIKUNJA_API_TOKEN")

ADGUARD_BASE_URL = _env("ADGUARD_BASE_URL")
ADGUARD_USERNAME = _env("ADGUARD_USERNAME")
ADGUARD_PASSWORD = _env("ADGUARD_PASSWORD")

CLOUDFLARE_API_TOKEN = _env("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = _env("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_TUNNEL_ID = _env("CLOUDFLARE_TUNNEL_ID")

NPM_BASE_URL = _env("NPM_BASE_URL")
NPM_EMAIL = _env("NPM_EMAIL")
NPM_PASSWORD = _env("NPM_PASSWORD")

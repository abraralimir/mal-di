"""Persist integration / connection-pool settings (UI-editable). Merges with .env defaults."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from config import Settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
SETTINGS_FILE = DATA_DIR / "integration_settings.json"


def _defaults_from_env(settings: Settings) -> Dict[str, Any]:
    return {
        "ibm_bpm": {
            "base_url": (settings.BPM_BASE_URL or "").strip(),
            "pool_connections": int(settings.BPM_POOL_CONNECTIONS),
            "pool_maxsize": int(settings.BPM_POOL_MAXSIZE),
            "http_timeout_sec": float(settings.BPM_HTTP_TIMEOUT_SEC),
            "username": (settings.BPM_USERNAME or "").strip(),
            "password": (settings.BPM_PASSWORD or "").strip(),
            "bearer_token": (settings.BPM_BEARER_TOKEN or "").strip(),
        },
        "filenet": {
            "base_url": (settings.FILENET_BASE_URL or "").strip(),
            "pool_connections": int(settings.FILENET_POOL_CONNECTIONS),
            "pool_maxsize": int(settings.FILENET_POOL_MAXSIZE),
            "http_timeout_sec": float(settings.FILENET_HTTP_TIMEOUT_SEC),
            "username": (settings.FILENET_USERNAME or "").strip(),
            "password": (settings.FILENET_PASSWORD or "").strip(),
            "bearer_token": (settings.FILENET_BEARER_TOKEN or "").strip(),
        },
    }


def _load_disk() -> Dict[str, Any]:
    if not SETTINGS_FILE.is_file():
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read %s: %s", SETTINGS_FILE, e)
        return {}


def _save_disk(data: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(SETTINGS_FILE)


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def read_effective(settings: Settings) -> Dict[str, Any]:
    """Env defaults overlaid by values saved from the UI."""
    return _deep_merge(_defaults_from_env(settings), _load_disk())


class ConnectorBlock(BaseModel):
    base_url: str = ""
    pool_connections: int = Field(10, ge=1, le=200)
    pool_maxsize: int = Field(32, ge=1, le=200)
    http_timeout_sec: float = Field(120.0, ge=5.0, le=900.0)
    username: str = ""
    password: str = "__KEEP__"
    bearer_token: str = "__KEEP__"


class IntegrationsSaveBody(BaseModel):
    ibm_bpm: ConnectorBlock
    filenet: ConnectorBlock


def _apply_block(stored: Dict[str, Any], block: ConnectorBlock) -> None:
    stored["base_url"] = (block.base_url or "").strip()
    stored["pool_connections"] = int(block.pool_connections)
    stored["pool_maxsize"] = int(block.pool_maxsize)
    stored["http_timeout_sec"] = float(block.http_timeout_sec)
    stored["username"] = (block.username or "").strip()
    if block.password != "__KEEP__":
        stored["password"] = block.password or ""
    if block.bearer_token != "__KEEP__":
        stored["bearer_token"] = block.bearer_token or ""


def save_integration_settings(settings: Settings, body: IntegrationsSaveBody) -> Dict[str, Any]:
    """Merge save body into effective config, write disk, caller reloads pools."""
    eff = read_effective(settings)
    _apply_block(eff["ibm_bpm"], body.ibm_bpm)
    _apply_block(eff["filenet"], body.filenet)
    _save_disk(eff)
    return eff


def public_view(effective: Dict[str, Any]) -> Dict[str, Any]:
    """Safe for GET / UI (no secrets)."""
    out: Dict[str, Any] = {}
    for key in ("ibm_bpm", "filenet"):
        b = effective.get(key, {})
        out[key] = {
            "base_url": b.get("base_url", ""),
            "pool_connections": int(b.get("pool_connections", 10)),
            "pool_maxsize": int(b.get("pool_maxsize", 32)),
            "http_timeout_sec": float(b.get("http_timeout_sec", 120.0)),
            "username": b.get("username", ""),
            "has_password": bool((b.get("password") or "").strip()),
            "has_bearer_token": bool((b.get("bearer_token") or "").strip()),
            "password": "__KEEP__",
            "bearer_token": "__KEEP__",
        }
    return out


def get_bpm_init_kwargs(settings: Settings) -> Optional[Dict[str, Any]]:
    cfg = read_effective(settings).get("ibm_bpm", {})
    url = (cfg.get("base_url") or "").strip()
    if not url:
        return None
    return {
        "label": "IBM_BPM",
        "base_url": url,
        "pool_connections": int(cfg.get("pool_connections", 10)),
        "pool_maxsize": int(cfg.get("pool_maxsize", 32)),
        "timeout_sec": float(cfg.get("http_timeout_sec", 120.0)),
        "username": (cfg.get("username") or "").strip() or None,
        "password": (cfg.get("password") or "").strip() or None,
        "bearer_token": (cfg.get("bearer_token") or "").strip() or None,
    }


def get_filenet_init_kwargs(settings: Settings) -> Optional[Dict[str, Any]]:
    cfg = read_effective(settings).get("filenet", {})
    url = (cfg.get("base_url") or "").strip()
    if not url:
        return None
    return {
        "label": "FILENET",
        "base_url": url,
        "pool_connections": int(cfg.get("pool_connections", 10)),
        "pool_maxsize": int(cfg.get("pool_maxsize", 32)),
        "timeout_sec": float(cfg.get("http_timeout_sec", 120.0)),
        "username": (cfg.get("username") or "").strip() or None,
        "password": (cfg.get("password") or "").strip() or None,
        "bearer_token": (cfg.get("bearer_token") or "").strip() or None,
    }

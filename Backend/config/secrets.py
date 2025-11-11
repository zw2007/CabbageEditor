from __future__ import annotations

"""
Secret management helper.

Secrets now live directly under Backend/config (plain-text `secrets.toml`), with
`mcp_client_secrets.json` kept for legacy tooling and `mcp_client_secrets_example.json`
as a template. This module exposes helper APIs used by infrastructure clients
(LLM, MCP) so the rest of the system never touches plaintext credentials directly.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import tomllib


CONFIG_SECRET_FILE = Path(__file__).with_name("secrets.toml")
PROJECT_SECRET_FILE = Path(__file__).with_name("mcp_client_secrets.json")
PROJECT_SECRET_TEMPLATE = Path(__file__).with_name("mcp_client_secrets_example.json")


@dataclass(frozen=True)
class SecretBundle:
    api_key: str | None
    base_url: str | None


def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        content = path.read_text(encoding="utf-8")
        if content.startswith("\ufeff"):
            content = content.lstrip("\ufeff")
        return tomllib.loads(content)
    except Exception:
        return {}


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_secret_bundle() -> SecretBundle:
    """
    Secrets now live inside Backend/config so deployments can manage them centrally.
    Lookup order:
    1. secrets.toml (authoritative, plain-text)
    2. mcp_client_secrets.json (legacy JSON file kept for compatibility)
    3. mcp_client_secrets_example.json (template / fallback)
    """
    data = _read_toml(CONFIG_SECRET_FILE)
    if data.get("api_key") and data.get("base_url"):
        return SecretBundle(api_key=data["api_key"], base_url=data["base_url"])

    legacy = _read_json(PROJECT_SECRET_FILE)
    if legacy.get("api_key") and legacy.get("base_url"):
        return SecretBundle(api_key=legacy["api_key"], base_url=legacy["base_url"])

    template = _read_json(PROJECT_SECRET_TEMPLATE)
    return SecretBundle(
        api_key=template.get("api_key"),
        base_url=template.get("base_url"),
    )


def ensure_config_secret_file() -> Path:
    """
    Create Backend/config/secrets.toml if it does not exist so tooling can edit it.
    """
    CONFIG_SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_SECRET_FILE.exists():
        CONFIG_SECRET_FILE.write_text('api_key = "xxx"\nbase_url = ""\n', encoding="utf-8")
    return CONFIG_SECRET_FILE


# Backwards compatibility for scripts that imported the old helper name.
ensure_user_secret_file = ensure_config_secret_file


__all__ = [
    "SecretBundle",
    "get_secret_bundle",
    "ensure_config_secret_file",
    "ensure_user_secret_file",
    "CONFIG_SECRET_FILE",
]

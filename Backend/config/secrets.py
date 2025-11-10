from __future__ import annotations

"""
Secret management helper.

Secrets are resolved lazily and prioritise environment variables, then a
user-level credential file (~/.coronaengine/credentials.toml), and finally the
project-level template (Backend/mcp_client_secrets_example.json).  The module
exposes helper APIs used by infrastructure clients (LLM, MCP) so the rest of
the system never touches plaintext credentials directly.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import os
import tomllib


USER_SECRET_FILE = Path.home() / ".coronaengine" / "credentials.toml"
PROJECT_SECRET_TEMPLATE = Path(__file__).resolve().parents[1] / "mcp_client_secrets_example.json"


@dataclass(frozen=True)
class SecretBundle:
    api_key: str | None
    base_url: str | None


def _read_user_secrets() -> dict:
    if USER_SECRET_FILE.exists():
        try:
            return tomllib.loads(USER_SECRET_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _read_project_template() -> dict:
    if PROJECT_SECRET_TEMPLATE.exists():
        try:
            return json.loads(PROJECT_SECRET_TEMPLATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def get_secret_bundle() -> SecretBundle:
    env_key = os.getenv("CORONA_API_KEY")
    env_base_url = os.getenv("CORONA_BASE_URL")
    if env_key and env_base_url:
        return SecretBundle(api_key=env_key, base_url=env_base_url)

    user_conf = _read_user_secrets()
    if "api_key" in user_conf and "base_url" in user_conf:
        return SecretBundle(api_key=user_conf["api_key"], base_url=user_conf["base_url"])

    template = _read_project_template()
    return SecretBundle(
        api_key=template.get("api_key"),
        base_url=template.get("base_url"),
    )


def ensure_user_secret_file() -> Path:
    """
    Create the ~/.coronaengine directory and credentials file if they do not exist.
    Returns the path so CLI tooling can guide the user.
    """
    USER_SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USER_SECRET_FILE.exists():
        USER_SECRET_FILE.write_text("api_key = \"\"\nbase_url = \"\"\n", encoding="utf-8")
    return USER_SECRET_FILE


__all__ = ["SecretBundle", "get_secret_bundle", "ensure_user_secret_file", "USER_SECRET_FILE"]

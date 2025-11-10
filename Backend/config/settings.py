from __future__ import annotations

"""
Central settings module for the refactored Backend runtime.

The new architecture treats configuration as immutable data classes that can be
queried by every layer (core/application/infrastructure).  Values come from,
in order of precedence:
1. Environment variables (prefixed with CORONA_*)
2. User-level config file (~/.coronaengine/config.toml)
3. Project-level config file (Backend/config/defaults.toml)

The settings object is cached per-process so components can just call
`get_settings()` without worrying about repeated IO or parsing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import tomllib

_SETTINGS: Optional["Settings"] = None


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@dataclass(frozen=True)
class SecretsConfig:
    """Where API keys and other credentials are stored."""

    api_key: str | None = None
    base_url: str | None = None


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "qwen"
    default_model: str = "Qwen/Qwen2.5-7B-Instruct"
    tool_model: str = "Qwen/Qwen3-14B"
    require_web_search: bool = True


@dataclass(frozen=True)
class PathsConfig:
    repo_root: Path
    backend_root: Path
    frontend_dist: Path
    script_dir: Path


@dataclass(frozen=True)
class Settings:
    secrets: SecretsConfig
    llm: LLMConfig
    paths: PathsConfig
    enable_gpu: bool = False
    log_level: str = "INFO"


def _load_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[2]
    backend_root = repo_root / "Backend"
    frontend_dist = repo_root / "Frontend" / "dist" / "index.html"
    script_dir = backend_root / "script"

    # load layered config
    defaults = _load_toml(backend_root / "config" / "defaults.toml")
    user_conf = _load_toml(Path.home() / ".coronaengine" / "config.toml")

    def _pick(key: str, default=None):
        env_key = f"CORONA_{key.upper()}"
        return os.getenv(env_key, user_conf.get(key, defaults.get(key, default)))

    secrets = SecretsConfig(
        api_key=_pick("api_key"),
        base_url=_pick("base_url"),
    )

    llm = LLMConfig(
        provider=_pick("llm_provider", "qwen"),
        default_model=_pick("llm_default_model", "Qwen/Qwen2.5-7B-Instruct"),
        tool_model=_pick("llm_tool_model", "Qwen/Qwen3-14B"),
        require_web_search=str(_pick("llm_require_search", "true")).lower() == "true",
    )

    paths = PathsConfig(
        repo_root=repo_root,
        backend_root=backend_root,
        frontend_dist=frontend_dist,
        script_dir=script_dir,
    )

    enable_gpu = str(_pick("enable_gpu", "false")).lower() == "true"
    log_level = str(_pick("log_level", "INFO")).upper()

    return Settings(
        secrets=secrets,
        llm=llm,
        paths=paths,
        enable_gpu=enable_gpu,
        log_level=log_level,
    )


def get_settings() -> Settings:
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = _load_settings()
    return _SETTINGS


__all__ = ["Settings", "SecretsConfig", "LLMConfig", "PathsConfig", "get_settings"]

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
import os
import tomllib

APP_CONFIG_FILE = Path(__file__).with_name("app_config.toml")
APP_CONFIG_TEMPLATE = Path(__file__).with_name("app_config.example.toml")
USER_CONFIG_FILE = Path.home() / ".coronaengine" / "app_config.toml"
DEFAULT_SYSTEM_PROMPT = (
    "你是 CabbageEditor 的内置助手。请在回答前检查可用工具，必要时调用 MCP、图像或视频工具；其余情况直接用中文简洁回答。"
)

_CACHE: Optional["AppConfig"] = None


# ---------------------------------------------------------------------------
# dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    type: str = "openai"
    base_url: str | None = None
    api_key: str | None = None
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatModelConfig:
    provider: str
    model: str
    temperature: float
    request_timeout: float
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


@dataclass(frozen=True)
class ToolModelConfig:
    provider: str
    model: str


@dataclass(frozen=True)
class MediaToolConfig:
    enable: bool = False
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None


@dataclass(frozen=True)
class MediaConfig:
    image: MediaToolConfig = MediaToolConfig()
    video: MediaToolConfig = MediaToolConfig()


@dataclass(frozen=True)
class RuntimeConfig:
    enable_gpu: bool = False
    log_level: str = "INFO"


@dataclass(frozen=True)
class PathsConfig:
    repo_root: Path
    backend_root: Path
    frontend_dist: Path
    script_dir: Path
    autosave_dir: Path


@dataclass(frozen=True)
class AppConfig:
    providers: Dict[str, ProviderConfig]
    chat: ChatModelConfig
    tool_models: Dict[str, ToolModelConfig]
    media: MediaConfig
    runtime: RuntimeConfig
    paths: PathsConfig


# ---------------------------------------------------------------------------
# file helpers
# ---------------------------------------------------------------------------


def _load_toml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _deep_merge(base: Dict[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _ensure_app_config_file() -> None:
    if APP_CONFIG_FILE.exists():
        return
    APP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if APP_CONFIG_TEMPLATE.exists():
        APP_CONFIG_FILE.write_text(APP_CONFIG_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        APP_CONFIG_FILE.write_text("", encoding="utf-8")


def _apply_env_overrides(data: Dict[str, Any]) -> None:
    overrides = {
        ("runtime", "enable_gpu"): os.getenv("CORONA_ENABLE_GPU"),
        ("runtime", "log_level"): os.getenv("CORONA_LOG_LEVEL"),
        ("llm", "chat", "model"): os.getenv("CORONA_LLM_MODEL"),
        ("llm", "chat", "provider"): os.getenv("CORONA_LLM_PROVIDER"),
    }
    for path, value in overrides.items():
        if value is None:
            continue
        section = data
        for part in path[:-1]:
            section = section.setdefault(part, {})
        key = path[-1]
        if key == "enable_gpu":
            section[key] = str(value).strip().lower() in {"1", "true", "yes", "on"}
        else:
            section[key] = value


def _load_config_data() -> Dict[str, Any]:
    _ensure_app_config_file()
    project = _load_toml(APP_CONFIG_FILE)
    user = _load_toml(USER_CONFIG_FILE)
    merged = _deep_merge(project, user)
    _apply_env_overrides(merged)
    return merged


# ---------------------------------------------------------------------------
# parsing helpers
# ---------------------------------------------------------------------------


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_providers(raw: Any) -> Dict[str, ProviderConfig]:
    providers: Dict[str, ProviderConfig] = {}
    entries = raw if isinstance(raw, list) else []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        name = entry.get("name")
        if not name:
            continue
        api_key = entry.get("api_key")
        api_key_env = entry.get("api_key_env")
        if api_key_env:
            api_key = os.getenv(str(api_key_env), api_key)
        headers = entry.get("headers") if isinstance(entry.get("headers"), Mapping) else {}
        providers[name] = ProviderConfig(
            name=name,
            type=str(entry.get("type", "openai")),
            base_url=entry.get("base_url"),
            api_key=api_key,
            headers={str(k): str(v) for k, v in headers.items()},
        )
    return providers


def _load_tool_models(raw: Mapping[str, Any]) -> Dict[str, ToolModelConfig]:
    tool_models: Dict[str, ToolModelConfig] = {}
    for name, cfg in raw.items():
        if not isinstance(cfg, Mapping):
            continue
        provider = cfg.get("provider")
        model = cfg.get("model")
        if not provider or not model:
            continue
        tool_models[name] = ToolModelConfig(provider=str(provider), model=str(model))
    return tool_models


def _load_media_config(raw: Mapping[str, Any]) -> MediaConfig:
    def _load_media_tool(section: Mapping[str, Any] | None) -> MediaToolConfig:
        if not isinstance(section, Mapping):
            return MediaToolConfig()
        return MediaToolConfig(
            enable=_as_bool(section.get("enable"), False),
            provider=section.get("provider"),
            model=section.get("model"),
            base_url=section.get("base_url"),
        )

    image = _load_media_tool(raw.get("image"))
    video = _load_media_tool(raw.get("video"))
    return MediaConfig(image=image, video=video)


# ---------------------------------------------------------------------------
# public load function
# ---------------------------------------------------------------------------


def _build_app_config() -> AppConfig:
    raw = _load_config_data()

    repo_root = Path(__file__).resolve().parents[3]
    backend_root = repo_root / "Backend"
    autosave_dir = repo_root / "autosave"
    autosave_dir.mkdir(parents=True, exist_ok=True)
    paths = PathsConfig(
        repo_root=repo_root,
        backend_root=backend_root,
        frontend_dist=repo_root / "Frontend" / "dist" / "index.html",
        script_dir=backend_root / "script",
        autosave_dir=autosave_dir,
    )

    providers = _load_providers(raw.get("providers"))
    if not providers:
        raise RuntimeError("app_config.toml 中至少需要声明一个 [[providers]]")

    llm_section = raw.get("llm", {})
    chat_section = llm_section.get("chat", llm_section)
    chat = ChatModelConfig(
        provider=str(chat_section.get("provider", next(iter(providers.keys())))),
        model=str(chat_section.get("model", "Qwen/Qwen2.5-7B-Instruct")),
        temperature=_as_float(chat_section.get("temperature", 0.2), 0.2),
        request_timeout=_as_float(chat_section.get("request_timeout", 60), 60.0),
        system_prompt=str(chat_section.get("system_prompt", DEFAULT_SYSTEM_PROMPT)),
    )

    tool_models = _load_tool_models(llm_section.get("tool_models", {}))

    media = _load_media_config(raw.get("media", {}))

    runtime_data = raw.get("runtime", {})
    runtime = RuntimeConfig(
        enable_gpu=_as_bool(runtime_data.get("enable_gpu"), False),
        log_level=str(runtime_data.get("log_level", "INFO")).upper(),
    )

    return AppConfig(
        providers=providers,
        chat=chat,
        tool_models=tool_models,
        media=media,
        runtime=runtime,
        paths=paths,
    )


def get_app_config() -> AppConfig:
    global _CACHE
    if _CACHE is None:
        _CACHE = _build_app_config()
    return _CACHE


def reload_app_config() -> AppConfig:
    global _CACHE
    _CACHE = _build_app_config()
    return _CACHE


__all__ = [
    "AppConfig",
    "ProviderConfig",
    "ChatModelConfig",
    "ToolModelConfig",
    "MediaConfig",
    "MediaToolConfig",
    "RuntimeConfig",
    "PathsConfig",
    "get_app_config",
    "reload_app_config",
]

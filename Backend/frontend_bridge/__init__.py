"""Qt WebChannel service adapters that bridge UI signals to application services."""

from importlib import import_module
from typing import Any

__all__ = [
    "AIService",
    "AppService",
    "ProjectService",
    "SceneService",
    "ScriptingService",
    "setup_webchannel_for_view",
    "teardown_webchannel_for_view",
]


_ATTR_MAP = {
    "AIService": ("Backend.frontend_bridge.ai", "AIService"),
    "AppService": ("Backend.frontend_bridge.app", "AppService"),
    "ProjectService": ("Backend.frontend_bridge.project", "ProjectService"),
    "SceneService": ("Backend.frontend_bridge.scene", "SceneService"),
    "ScriptingService": ("Backend.frontend_bridge.scripting", "ScriptingService"),
    "setup_webchannel_for_view": ("Backend.frontend_bridge.webchannel", "setup_webchannel_for_view"),
    "teardown_webchannel_for_view": ("Backend.frontend_bridge.webchannel", "teardown_webchannel_for_view"),
}


def __getattr__(name: str) -> Any:
    if name not in _ATTR_MAP:
        raise AttributeError(f"module 'Backend.frontend_bridge' has no attribute '{name}'")
    module_name, attr = _ATTR_MAP[name]
    module = import_module(module_name)
    value = getattr(module, attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(__all__) + list(globals().keys()))

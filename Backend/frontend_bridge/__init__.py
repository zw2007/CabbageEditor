"""Qt WebChannel service adapters that bridge UI signals to application services."""

from importlib import import_module
from typing import Any, TYPE_CHECKING

_ATTR_MAP = {
    "AIService": ("Backend.frontend_bridge.ai", "AIService"),
    "AppService": ("Backend.frontend_bridge.app", "AppService"),
    "ProjectService": ("Backend.frontend_bridge.project", "ProjectService"),
    "SceneService": ("Backend.frontend_bridge.scene", "SceneService"),
    "ScriptingService": ("Backend.frontend_bridge.scripting", "ScriptingService"),
    "setup_webchannel_for_view": ("Backend.frontend_bridge.webchannel", "setup_webchannel_for_view"),
    "teardown_webchannel_for_view": ("Backend.frontend_bridge.webchannel", "teardown_webchannel_for_view"),
}

__all__ = list(_ATTR_MAP.keys())

if TYPE_CHECKING:
    # 仅供类型检查器/IDE 使用，运行时不执行这些导入
    from Backend.frontend_bridge.ai import AIService  # type: ignore
    from Backend.frontend_bridge.app import AppService  # type: ignore
    from Backend.frontend_bridge.project import ProjectService  # type: ignore
    from Backend.frontend_bridge.scene import SceneService  # type: ignore
    from Backend.frontend_bridge.scripting import ScriptingService  # type: ignore
    from Backend.frontend_bridge.webchannel import setup_webchannel_for_view, \
        teardown_webchannel_for_view  # type: ignore


def __getattr__(name: str) -> Any:
    if name not in _ATTR_MAP:
        raise AttributeError(f"module 'Backend.frontend_bridge' has no attribute '{name}'")
    module_name, attr = _ATTR_MAP[name]
    module = import_module(module_name)
    value = getattr(module, attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)

from __future__ import annotations

from typing import List

from langchain_core.tools import BaseTool

from Backend.artificial_intelligence.config.config import AppConfig
from Backend.artificial_intelligence.tools.mcp.scene_tools import load_scene_tools


def load_mcp_tools(config: AppConfig) -> list[BaseTool]:
    return _load_internal_scene_tools()


def _load_internal_scene_tools() -> List[BaseTool]:
    from Backend.utils.bootstrap import bootstrap
    from Backend.utils.container import get_container

    bootstrap()
    container = get_container()
    try:
        scene_service = container.resolve("scene_service")
    except KeyError:
        return []
    return load_scene_tools(scene_service)


__all__ = ["load_mcp_tools"]

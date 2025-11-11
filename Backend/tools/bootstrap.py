from __future__ import annotations

from Backend.engine_core.services.scene_service import SceneApplicationService
from Backend.engine_core.services.project_service import ProjectApplicationService
from Backend.artificial_intelligence.services import AIApplicationService
from Backend.artificial_intelligence.adapters import MCPToolAdapter
from Backend.engine_core.scene_manager import SceneManager
from Backend.artificial_intelligence.foundation_api import LLMClient
from Backend.network_service.mcp import server as mcp_server
from Backend.shared.container import get_container
from Backend.shared.logging import configure_logging


def bootstrap() -> None:
    container = get_container()
    if container.get_flag("bootstrapped"):
        return
    configure_logging()

    container.register("scene_manager", SceneManager)
    container.register("scene_service", lambda: SceneApplicationService(container.resolve("scene_manager")))
    container.register(
        "project_service",
        lambda: ProjectApplicationService(container.resolve("scene_service")),
    )
    mcp_server.set_scene_service(container.resolve("scene_service"))
    container.register("tool_adapter", lambda: MCPToolAdapter(mcp_server.app))
    container.register("llm_client", lambda: LLMClient(container.resolve("tool_adapter")))
    container.register(
        "ai_service",
        lambda: AIApplicationService(container.resolve("llm_client")),
    )
    container.set_flag("bootstrapped", True)


__all__ = ["bootstrap"]

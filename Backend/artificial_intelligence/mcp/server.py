from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from mcp.server.fastmcp import FastMCP, Context

from Backend.utils.scene_service import SceneApplicationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TransformMCPServer")

scene_service: SceneApplicationService | None = None


def set_scene_service(service: SceneApplicationService) -> None:
    global scene_service
    scene_service = service


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    logger.info("TransformMCP server starting up")
    try:
        yield {}
    finally:
        logger.info("TransformMCP server shut down")


app = FastMCP("TransformMCP", lifespan=server_lifespan)


@app.tool()
async def transform_actor(
    actor_name: str,
    operation: str,
    x: float,
    y: float,
    z: float,
    scene_name: str = "MainScene",
) -> str:
    if scene_service is None:
        raise RuntimeError("Scene service not configured")
    payload = scene_service.apply_transform(scene_name, actor_name, operation, [x, y, z])
    return json.dumps(payload)


@app.tool()
async def list_actors(scene_name: str) -> str:
    if scene_service is None:
        raise RuntimeError("Scene service not configured")
    data = scene_service.repository.get(scene_name)
    if not data:
        return json.dumps({"scene": scene_name, "actors": []})
    actors = [actor.name for actor in data.list_actors()]
    return json.dumps({"scene": scene_name, "actors": actors})


def main() -> None:
    app.run()


__all__ = ["app", "main"]

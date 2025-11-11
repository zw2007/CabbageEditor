"""FastMCP server that exposes engine tooling over the MCP protocol."""

from .server import app, main, set_scene_service

__all__ = ["app", "main", "set_scene_service"]

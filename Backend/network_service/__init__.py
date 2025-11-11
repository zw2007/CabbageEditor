"""Collaboration and network-facing services (LAN/WAN/MCP)."""

from .mcp.server import app as mcp_app

__all__ = ["mcp_app"]

from __future__ import annotations

import anyio
import json
from contextlib import asynccontextmanager
from typing import Dict, List, Tuple, Optional

from mcp import ClientSession
from mcp.server.fastmcp import FastMCP

from Backend.artificial_intelligence.foundation_api import ToolAdapter
from Backend.artificial_intelligence.mcp.server import app as server_app


@asynccontextmanager
async def create_internal_connection(app: FastMCP):
    client_to_server_writer, client_to_server_reader = anyio.create_memory_object_stream(0)
    server_to_client_writer, server_to_client_reader = anyio.create_memory_object_stream(0)

    async def run_server_task():
        await app._mcp_server.run(
            client_to_server_reader,
            server_to_client_writer,
            app._mcp_server.create_initialization_options(),
        )

    async with anyio.create_task_group() as tg:
        tg.start_soon(run_server_task)
        try:
            yield server_to_client_reader, client_to_server_writer
        finally:
            tg.cancel_scope.cancel()


class MCPToolAdapter(ToolAdapter):
    def __init__(self, app: FastMCP | None = None):
        self.app = app or server_app

    def list_tools(self) -> List[Dict]:
        return anyio.run(self._list_tools_async)

    async def _list_tools_async(self) -> List[Dict]:
        async with create_internal_connection(self.app) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                response = await session.list_tools()
                tools = []
                for tool in response.tools:
                    parameters = getattr(tool, "input_schema", None)
                    if parameters is None:
                        if hasattr(tool, "model_dump"):
                            data = tool.model_dump()
                        elif hasattr(tool, "dict"):
                            data = tool.dict()
                        else:
                            data = getattr(tool, "__dict__", {})
                        parameters = (
                            data.get("input_schema")
                            or data.get("inputSchema")
                            or data.get("input_schema_json_schema")
                            or {}
                        )
                    tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": getattr(tool, "name", "unknown_tool"),
                                "description": getattr(tool, "description", ""),
                                "parameters": parameters,
                            },
                        }
                    )
                return tools

    def call_tool(self, name: str, arguments: Dict) -> str:
        return anyio.run(self._call_tool_async, name, arguments)

    async def _call_tool_async(self, name: str, arguments: Dict) -> str:
        async with create_internal_connection(self.app) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                response = await session.call_tool(name, arguments)
                return response.content[0].text if response.content else ""


__all__ = ["MCPToolAdapter"]

"""Utility entrypoints and fallbacks for running Corona backend tooling."""

from .bootstrap import bootstrap
from .mcp_client import main as run_mcp_client
from .transform_server import main as run_transform_server

__all__ = ["bootstrap", "run_mcp_client", "run_transform_server"]

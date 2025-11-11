"""Utility entrypoints and fallbacks for running Corona backend tooling."""

from .bootstrap import bootstrap
from .central_manager import CentralManager
from .dialogs import FileHandler
from .static_components import url

__all__ = ["bootstrap", "CentralManager", "FileHandler", "url"]

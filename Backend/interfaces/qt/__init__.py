"""Qt-specific adapters (WebChannel, static assets, dock helpers, etc.)."""

from .central_manager import CentralManager
from .static_components import url
from .webchannel import setup_webchannel_for_view, teardown_webchannel_for_view

__all__ = [
    "CentralManager",
    "setup_webchannel_for_view",
    "teardown_webchannel_for_view",
    "url",
]

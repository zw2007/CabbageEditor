"""Bridges between Python and the embedded frontend (Qt WebChannel, JS helpers)."""

from .webchannel import setup_webchannel_for_view, teardown_webchannel_for_view, WebChannelContext

__all__ = [
    "WebChannelContext",
    "setup_webchannel_for_view",
    "teardown_webchannel_for_view",
]

"""Unified entry points for foundational model APIs (LLMs, embeddings, etc.)."""

from .client import LLMClient, ToolAdapter

__all__ = ["LLMClient", "ToolAdapter"]

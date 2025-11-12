from __future__ import annotations

from typing import Any, Dict, List, Optional
import json

from openai import OpenAI

from Backend.config.settings import get_settings
from Backend.config.secrets import get_secret_bundle
from Backend.artificial_intelligence.core import Conversation
from Backend.shared.logging import get_logger


logger = get_logger(__name__)


class ToolAdapter:
    def list_tools(self) -> List[Dict[str, Any]]:
        return []

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        raise NotImplementedError


class LLMClient:
    def __init__(self, tool_adapter: ToolAdapter | None = None) -> None:
        settings = get_settings()
        secrets = get_secret_bundle()
        if not secrets.api_key or not secrets.base_url:
            raise RuntimeError(
                "Missing API credentials. Configure CORONA_API_KEY/BASE_URL or ~/.coronaengine/credentials.toml"
            )
        self.client = OpenAI(api_key=secrets.api_key, base_url=secrets.base_url)
        self.tool_adapter = tool_adapter
        self.settings = settings.llm

    def _build_messages(self, conversation: Conversation) -> List[Dict[str, str]]:
        messages = conversation.to_openai_payload()
        if self.settings.require_web_search:
            instruction = (
                "Before answering, call the `web_search` tool with the user's question to fetch fresh information."
            )
            messages = [{"role": "system", "content": instruction}] + messages
        return messages

    def complete(self, conversation: Conversation) -> str:
        messages = self._build_messages(conversation)
        tools = self.tool_adapter.list_tools() if self.tool_adapter else None
        response = self.client.chat.completions.create(
            model=self.settings.default_model,
            messages=messages,
            tools=tools,
        )
        choice = response.choices[0]
        if choice.finish_reason == "tool_calls" and self.tool_adapter:
            tool_call = choice.message.tool_calls[0]
            result = self.tool_adapter.call_tool(
                tool_call.function.name,
                json.loads(tool_call.function.arguments),
            )
            conversation.add_assistant(result)
            follow_up = self.client.chat.completions.create(
                model=self.settings.default_model,
                messages=conversation.to_openai_payload(),
            )
            return follow_up.choices[0].message.content or ""
        return choice.message.content or ""


__all__ = ["LLMClient", "ToolAdapter"]

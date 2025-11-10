from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class Conversation:
    """Represents a stateful AI conversation."""

    messages: List[ChatMessage] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.messages.append(ChatMessage(role="user", content=content))

    def add_system(self, content: str) -> None:
        self.messages.append(ChatMessage(role="system", content=content))

    def add_assistant(self, content: str) -> None:
        self.messages.append(ChatMessage(role="assistant", content=content))

    def to_openai_payload(self) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]


__all__ = ["Conversation", "ChatMessage"]

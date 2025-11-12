from __future__ import annotations

import json
import time
from typing import Callable, Optional

from Backend.artificial_intelligence.core import Conversation
from Backend.artificial_intelligence.foundation_api import LLMClient
from Backend.utils.logging import get_logger


logger = get_logger(__name__)


class AIApplicationService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()
        self.conversation = Conversation()
        self.conversation.add_system(
            "You are a helpful assistant with access to CoronaEngine tooling. "
            "Always consider available tools before responding."
        )

    def ask(self, message: str, callback: Optional[Callable[[str], None]] = None) -> str:
        self.conversation.add_user(message)
        response = self.llm.complete(self.conversation)
        self.conversation.add_assistant(response)
        payload = json.dumps(
            {
                "type": "ai_response",
                "content": response,
                "status": "success",
                "timestamp": int(time.time()),
            }
        )
        if callback:
            callback(payload)
        logger.info("AI response generated")
        return payload

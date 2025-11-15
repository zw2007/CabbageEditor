
from __future__ import annotations
import json
import time
from typing import Any, Dict, List
from langchain_core.messages import BaseMessage, AIMessage
from Backend.artificial_intelligence.agent.agent import create_default_agent
from Backend.artificial_intelligence.config.config import get_app_config
from Backend.artificial_intelligence.models.models import get_chat_model

_CONVERSATION: List[Dict[str, Any]] = []


def _extract_text(messages: List[Any]) -> str:
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, BaseMessage):
        content = last.content
        return content if isinstance(content, str) else str(content)
    if isinstance(last, dict):
        return str(last.get("content", ""))
    return str(last)


def invoke_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    agent = create_default_agent()
    result = agent.invoke({"messages": messages})
    _log_ai_messages(result)
    return result


def handle_user_message(message: str) -> str:
    global _CONVERSATION
    current_history = list(_CONVERSATION)
    current_history.append({"role": "user", "content": message})
    state = invoke_messages(current_history)
    if isinstance(state, dict):
        messages = state.get("messages", [])
    else:
        messages = [state]
    content = _extract_text(messages)
    if not content.strip():
        content = _fallback_completion(current_history)
    _CONVERSATION = current_history + [{"role": "assistant", "content": content}]
    payload = {
        "type": "ai_response",
        "content": content,
        "status": "success",
        "timestamp": int(time.time()),
    }
    return json.dumps(payload, ensure_ascii=False)


def _fallback_completion(history: List[Dict[str, Any]]) -> str:
    cfg = get_app_config()
    chat_cfg = cfg.chat
    llm = get_chat_model(
        cfg,
        provider_name=chat_cfg.provider,
        model_name=chat_cfg.model,
        temperature=chat_cfg.temperature,
        request_timeout=chat_cfg.request_timeout,
    )
    prompt_messages: List[Dict[str, Any]] = [{"role": "system", "content": chat_cfg.system_prompt}, *history]
    ai_message = llm.invoke(prompt_messages)
    content = ai_message.content or ""
    print(f"[AIMessage] {content}")
    return content


def _log_ai_messages(payload: Any) -> None:
    messages = None
    if isinstance(payload, dict):
        messages = payload.get("messages")
    elif isinstance(payload, list):
        messages = payload
    if not isinstance(messages, list):
        return
    for msg in messages:
        if isinstance(msg, AIMessage):
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            print(f"[AIMessage] {text}")

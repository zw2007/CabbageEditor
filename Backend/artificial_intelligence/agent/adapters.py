from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, messages_to_dict

from Backend.artificial_intelligence.agent.requests import IncomingRequest
from Backend.artificial_intelligence.tools.image_handler import (
    load_image_data_url,
    path_to_url,
)


def extract_text(messages: List[Any]) -> str:
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, BaseMessage):
        return render_message_content(last.content)
    if isinstance(last, dict):
        content = last.get("content")
        return render_message_content(content)
    return str(last)


def build_user_message(request: IncomingRequest, uploads: List[str]) -> Dict[str, Any]:
    blocks: List[Dict[str, str]] = []
    text = request.text.strip()
    if text:
        blocks.append({"type": "text", "text": text})
    for note in uploads:
        blocks.append({"type": "text", "text": note})
    if not blocks:
        blocks.append({"type": "text", "text": "[图片上传]"})
    return {"role": "user", "content": blocks}


def coerce_messages(state: Any) -> List[Any]:
    if isinstance(state, dict):
        messages = state.get("messages", [])
    else:
        messages = state
    if isinstance(messages, list):
        return messages
    if messages is None:
        return []
    return [messages]


def convert_messages_for_history(messages: List[Any]) -> List[Dict[str, Any]]:
    if not messages:
        return []
    if all(isinstance(msg, BaseMessage) for msg in messages):
        return messages_to_dict(messages)  # type: ignore[arg-type]
    converted: List[Dict[str, Any]] = []
    for msg in messages:
        if isinstance(msg, dict):
            converted.append(msg)
        elif isinstance(msg, BaseMessage):
            converted.extend(messages_to_dict([msg]))
        else:
            converted.append({"role": "assistant", "content": str(msg)})
    return converted


def normalize_history_entries(messages: Sequence[Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for message in messages:
        normalized_message = _coerce_history_entry(message)
        if normalized_message is not None:
            normalized.append(normalized_message)
    return normalized


def sanitize_history_payloads(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized: List[Dict[str, Any]] = []
    for entry in messages:
        new_entry = dict(entry)
        content = new_entry.get("content")
        if isinstance(content, str):
            new_entry["content"] = summarize_payload_text(content, strip_images=True)
        elif isinstance(content, list):
            trimmed_blocks: List[Any] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image" and block.get("base64"):
                    block = dict(block)
                    block.pop("base64", None)
                trimmed_blocks.append(block)
            new_entry["content"] = trimmed_blocks
        sanitized.append(new_entry)
    return sanitized


def render_message_content(content: Any) -> str:
    if isinstance(content, str):
        return summarize_payload_text(content)
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and block.get("text"):
                    parts.append(str(block["text"]))
                elif block.get("type") == "image" and block.get("url"):
                    parts.append(f"[image] {block['url']}")
                elif block.get("type") == "image" and block.get("base64"):
                    parts.append("[image]")
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join([item for item in parts if item])
    if content is None:
        return ""
    return summarize_payload_text(str(content))


def extract_image_payload(messages: Sequence[Any]) -> Dict[str, Any] | None:
    ordered = list(messages)
    for message in reversed(ordered):
        if isinstance(message, ToolMessage):
            content = render_message_content(message.content)
            try:
                data = json.loads(content)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("type") == "image":
                if "image_base64" not in data:
                    data_url = load_image_data_url(data.get("image_url") or data.get("image_path"))
                    if data_url:
                        data["image_base64"] = data_url
                if "image_url" not in data:
                    url = path_to_url(data.get("image_path"))
                    if url:
                        data["image_url"] = url
                return data
    return None


def summarize_payload_text(text: str, strip_images: bool = False) -> str:
    text = text.strip()
    if not text:
        return text
    if text.startswith("{") and '"image_base64"' in text:
        try:
            data = json.loads(text)
        except Exception:
            if strip_images:
                return "[image payload omitted]"
            return text
        if isinstance(data, dict) and "image_base64" in data:
            name = data.get("image_name") or data.get("image_path") or data.get("prompt") or "image"
            data = dict(data)
            data.pop("image_base64", None)
            summary = f"[image payload: {name}]"
            return json.dumps(data, ensure_ascii=False) if not strip_images else summary
    if strip_images and "data:image" in text:
        return "[image payload omitted]"
    return text


def log_ai_messages(payload: Any) -> None:
    messages = None
    if isinstance(payload, dict):
        messages = payload.get("messages")
    elif isinstance(payload, list):
        messages = payload
    if not isinstance(messages, list):
        return
    for msg in messages:
        if isinstance(msg, AIMessage):
            text = render_message_content(msg.content)
            print(f"[AIMessage] {text}")
        elif isinstance(msg, ToolMessage):
            text = render_message_content(msg.content)
            tool_name = getattr(msg, "name", None) or "tool"
            print(f"[ToolMessage:{tool_name}] {text}")


def _coerce_history_entry(message: Any) -> Dict[str, Any] | None:
    if isinstance(message, BaseMessage):
        return _base_message_to_chat_dict(message)
    if isinstance(message, dict):
        if "role" in message and "content" in message:
            return message
        if "type" in message and "data" in message:
            return _message_dict_to_chat_dict(message)
        if "content" in message:
            role = str(message.get("role") or "assistant")
            return {"role": role, "content": message.get("content")}
        return None
    if isinstance(message, str):
        return {"role": "assistant", "content": message}
    return None


def _message_dict_to_chat_dict(message: Dict[str, Any]) -> Dict[str, Any]:
    msg_type = str(message.get("type") or "")
    data = dict(message.get("data") or {})
    role = _message_type_to_role(msg_type)
    content = data.get("content")
    normalized: Dict[str, Any] = {"role": role, "content": content}
    name = data.get("name")
    if name:
        normalized["name"] = name
    tool_call_id = data.get("tool_call_id")
    if tool_call_id:
        normalized["tool_call_id"] = tool_call_id
    additional = dict(data.get("additional_kwargs") or {})
    tool_calls = additional.pop("tool_calls", None)
    if tool_calls:
        normalized["tool_calls"] = tool_calls
    function_call = additional.pop("function_call", None)
    if function_call:
        normalized["function_call"] = function_call
    if additional:
        normalized["additional_kwargs"] = additional
    return normalized


def _base_message_to_chat_dict(message: BaseMessage) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "role": _message_type_to_role(getattr(message, "type", None)),
        "content": message.content,
    }
    name = getattr(message, "name", None)
    if name:
        normalized["name"] = name
    if isinstance(message, ToolMessage):
        if getattr(message, "tool_call_id", None):
            normalized["tool_call_id"] = message.tool_call_id
    additional = dict(getattr(message, "additional_kwargs", {}) or {})
    tool_calls = additional.pop("tool_calls", None)
    if tool_calls:
        normalized["tool_calls"] = tool_calls
    function_call = additional.pop("function_call", None)
    if function_call:
        normalized["function_call"] = function_call
    if additional:
        normalized["additional_kwargs"] = additional
    return normalized


def _message_type_to_role(value: str | None) -> str:
    mapping = {
        "human": "user",
        "user": "user",
        "ai": "assistant",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
        "function": "tool",
    }
    return mapping.get((value or "").lower(), value or "assistant")


__all__ = [
    "extract_text",
    "build_user_message",
    "coerce_messages",
    "convert_messages_for_history",
    "normalize_history_entries",
    "sanitize_history_payloads",
    "render_message_content",
    "extract_image_payload",
    "summarize_payload_text",
    "log_ai_messages",
]

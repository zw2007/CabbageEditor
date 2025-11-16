from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from Backend.artificial_intelligence.agent.executor import run_agent
from Backend.artificial_intelligence.agent.conversation import default_session_id, get_history, update_history
from Backend.artificial_intelligence.agent.adapters import (
    build_user_message,
    coerce_messages,
    convert_messages_for_history,
    extract_image_payload,
    extract_text,
    log_ai_messages,
    normalize_history_entries,
    sanitize_history_payloads,
)
from Backend.artificial_intelligence.config.config import get_app_config
from Backend.artificial_intelligence.models import get_chat_model
from Backend.artificial_intelligence.tools.storage import get_image_store
from Backend.artificial_intelligence.tools.session import reset_current_session, set_current_session
from Backend.utils.bootstrap import bootstrap

from Backend.artificial_intelligence.agent.requests import (
    normalize_request,
    normalize_upload_request,
)
from Backend.artificial_intelligence.tools.image_handler import register_uploads

bootstrap()
_IMAGE_STORE = get_image_store()


def invoke_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    result = run_agent(messages)
    log_ai_messages(result)
    return result


def handle_image_upload(payload: Any) -> str:
    request = normalize_upload_request(payload, default_session_id())
    stored = _IMAGE_STORE.save_upload(
        session_id=request.session_id,
        data=request.data,
        category=request.category,
        original_name=request.name,
    )
    url = _IMAGE_STORE.build_url(stored)
    response = {
        "type": "image_upload",
        "status": "success",
        "timestamp": int(time.time()),
        "session_id": request.session_id,
        "token": request.token,
        "image": {
            "name": stored.name,
            "url": url,
            "category": request.category,
        },
    }
    return json.dumps(response, ensure_ascii=False)


def handle_user_message(message: Any) -> str:
    request = normalize_request(message, default_session_id())
    stored_history = get_history(request.session_id)
    history = normalize_history_entries(stored_history)
    upload_notes = register_uploads(request)
    user_message = build_user_message(request, upload_notes)
    pending_history = [*history, user_message]

    token = set_current_session(request.session_id)
    try:
        state = invoke_messages(pending_history)
    finally:
        reset_current_session(token)

    messages = coerce_messages(state)
    history_extension = convert_messages_for_history(messages)
    history_extension = sanitize_history_payloads(history_extension)
    update_history(request.session_id, [*pending_history, *history_extension])

    content = extract_text(messages)
    if not content.strip():
        content = _fallback_completion(pending_history)

    image_payload = extract_image_payload(messages)
    payload: Dict[str, Any] = {
        "type": image_payload.get("type", "ai_response") if image_payload else "ai_response",
        "content": content,
        "status": "success",
        "timestamp": int(time.time()),
        "session_id": request.session_id,
    }
    if image_payload:
        payload.update(
            {
                "image_base64": image_payload.get("image_base64"),
                "image_name": image_payload.get("image_name"),
                "image_path": image_payload.get("image_path"),
                "image_url": image_payload.get("image_url"),
            }
        )
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


__all__ = ["invoke_messages", "handle_user_message", "handle_image_upload"]

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import List

from Backend.artificial_intelligence.agent.requests import IncomingRequest
from Backend.artificial_intelligence.tools.storage import (
    AUTOSAVE_URL_SCHEME,
    StoredImage,
    get_image_store,
)

_IMAGE_STORE = get_image_store()


def register_uploads(request: IncomingRequest) -> List[str]:
    notes: List[str] = []
    for attachment in request.images:
        stored = None
        if attachment.data:
            stored = _IMAGE_STORE.save_upload(
                session_id=request.session_id,
                data=attachment.data,
                category=attachment.category,
                original_name=attachment.name,
            )
        elif attachment.url:
            stored = _IMAGE_STORE.resolve_url(attachment.url)
            if stored and stored.session_id != request.session_id:
                stored = clone_image_to_session(stored, request.session_id, attachment.category)
        if stored:
            _IMAGE_STORE.register_reference(request.session_id, attachment.category, stored)
            url = _IMAGE_STORE.build_url(stored)
            notes.append(f"已上传{_category_label(attachment.category)}图片：{url}")
        elif attachment.url:
            notes.append(f"引用{_category_label(attachment.category)}图片：{attachment.url}")
    return notes


def load_image_data_url(path_str: str | None) -> str | None:
    if not path_str:
        return None
    if path_str.startswith(AUTOSAVE_URL_SCHEME):
        stored = _IMAGE_STORE.resolve_url(path_str)
        path = stored.path if stored else None
    else:
        path = Path(path_str)
    if path is None or not path.exists():
        return None
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def path_to_url(path_str: str | None) -> str | None:
    if not path_str:
        return None
    path = Path(path_str).resolve()
    try:
        relative = path.relative_to(_IMAGE_STORE.root)
    except ValueError:
        return None
    return f"{AUTOSAVE_URL_SCHEME}{relative.as_posix()}"


def clone_image_to_session(stored: StoredImage | None, session_id: str, category: str):
    if stored is None:
        raise ValueError("无法克隆不存在的图片")
    return _IMAGE_STORE.save_upload(
        session_id=session_id,
        data=stored.data_url,
        category=category or stored.category,
        original_name=stored.name,
    )


def _category_label(category: str) -> str:
    return {"product": "产品", "scene": "场景"}.get(category, category or "图片")


__all__ = [
    "register_uploads",
    "load_image_data_url",
    "path_to_url",
    "clone_image_to_session",
]

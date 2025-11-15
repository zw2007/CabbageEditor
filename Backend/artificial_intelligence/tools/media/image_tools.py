from __future__ import annotations

from langchain.tools import tool

from Backend.artificial_intelligence.config.config import AppConfig, MediaToolConfig


def load_image_tools(config: AppConfig) -> list:
    image_cfg = config.media.image
    if not _is_media_tool_enabled(image_cfg, config):
        return []

    provider = config.providers[image_cfg.provider]  # already validated
    model = image_cfg.model  # already validated

    @tool
    def generate_image(prompt: str) -> str:
        """根据描述生成一张图片（当前为占位实现）。"""
        return f"[{provider.name}:{model}] 图像生成占位响应：{prompt}"

    return [generate_image]


def _is_media_tool_enabled(cfg: MediaToolConfig, config: AppConfig) -> bool:
    if not cfg.enable:
        return False
    if not cfg.provider or not cfg.model:
        return False
    if cfg.provider not in config.providers:
        return False
    provider = config.providers[cfg.provider]
    return bool(provider.api_key)


__all__ = ["load_image_tools"]

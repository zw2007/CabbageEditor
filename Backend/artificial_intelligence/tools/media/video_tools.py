from __future__ import annotations

from langchain.tools import tool

from Backend.artificial_intelligence.config.config import AppConfig, MediaToolConfig


def load_video_tools(config: AppConfig) -> list:
    video_cfg = config.media.video
    if not _is_media_tool_enabled(video_cfg, config):
        return []

    provider = config.providers[video_cfg.provider]
    model = video_cfg.model

    @tool
    def generate_video(prompt: str) -> str:
        """根据描述生成短视频（当前为占位实现）。"""
        return f"[{provider.name}:{model}] 视频生成占位响应：{prompt}"

    return [generate_video]


def _is_media_tool_enabled(cfg: MediaToolConfig, config: AppConfig) -> bool:
    if not cfg.enable:
        return False
    if not cfg.provider or not cfg.model:
        return False
    if cfg.provider not in config.providers:
        return False
    provider = config.providers[cfg.provider]
    return bool(provider.api_key)


__all__ = ["load_video_tools"]

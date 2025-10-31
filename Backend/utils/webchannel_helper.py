from __future__ import annotations
import typing as _t
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject

# 直接在此维护 SceneManager 单例，避免依赖 Bridge
from .scene_manager import SceneManager


class WebChannelContext:
    def __init__(self, channel: QWebChannel, services: dict[str, QObject] | None = None) -> None:
        self.channel = channel
        self.services = services or {}


_scene_manager_singleton: SceneManager | None = None

def _get_scene_manager() -> SceneManager:
    global _scene_manager_singleton
    if _scene_manager_singleton is None:
        _scene_manager_singleton = SceneManager()
    return _scene_manager_singleton


def setup_webchannel_for_view(
    view: QWebEngineView,
    central_manager: object | None,
    *,
    register_services: bool = False,
    on_create_route: _t.Callable | None = None,
    on_remove_route: _t.Callable | None = None,
    on_message_to_dock: _t.Callable[[str, str], None] | None = None,
    on_command_to_main: _t.Callable[[str, str], None] | None = None,
) -> WebChannelContext:
    channel = QWebChannel()

    services: dict[str, QObject] = {}

    if register_services:
        try:
            from Backend.services.scene import SceneService
            from Backend.services.ai import AIService
            from Backend.services.scripting import ScriptingService
            from Backend.services.project import ProjectService
            from Backend.services.app import AppService

            scene_service = SceneService(_get_scene_manager(), None)
            ai_service = AIService(None)
            scripting_service = ScriptingService(None)
            project_service = ProjectService(scene_service, None)
            app_service = AppService(None)

            channel.registerObject("sceneService", scene_service)
            channel.registerObject("aiService", ai_service)
            channel.registerObject("scriptingService", scripting_service)
            channel.registerObject("projectService", project_service)
            channel.registerObject("appService", app_service)

            # AppService -> UI 回调（优先使用传入回调，其次尝试 central_manager）
            if on_create_route is not None:
                app_service.create_route_requested.connect(on_create_route)
            if on_remove_route is not None:
                app_service.remove_route_requested.connect(on_remove_route)
            if on_message_to_dock is not None:
                app_service.message_to_dock_requested.connect(on_message_to_dock)
            elif central_manager is not None and hasattr(central_manager, 'send_json_to_dock'):
                app_service.message_to_dock_requested.connect(lambda name, data: central_manager.send_json_to_dock(name, data))
            if on_command_to_main is not None:
                app_service.command_to_main_requested.connect(on_command_to_main)

            services = {
                "sceneService": scene_service,
                "aiService": ai_service,
                "scriptingService": scripting_service,
                "projectService": project_service,
                "appService": app_service,
            }
        except Exception as e:
            print(f"[WARN] 注册服务对象失败: {e}")

    try:
        view.page().setWebChannel(channel)
    except Exception:
        pass

    return WebChannelContext(channel=channel, services=services)


def teardown_webchannel_for_view(view: QWebEngineView, ctx: WebChannelContext) -> None:
    """解除绑定和清理：注销所有注册到 channel 的服务。"""
    try:
        if ctx and ctx.channel and ctx.services:
            for obj in ctx.services.values():
                try:
                    ctx.channel.deregisterObject(obj)
                except Exception:
                    pass
    except Exception:
        pass
    try:
        if ctx and ctx.channel:
            ctx.channel.deleteLater()
    except Exception:
        pass

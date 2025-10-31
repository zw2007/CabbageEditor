from __future__ import annotations
import typing as _t
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject

from .bridge import get_bridge


class WebChannelContext:
    """
    持有一次注册中创建的对象，便于调用方保存和清理。
    """

    def __init__(self, channel: QWebChannel, bridge: QObject,
                 services: dict[str, QObject] | None = None) -> None:
        self.channel = channel
        self.bridge = bridge
        self.services = services or {}


def setup_webchannel_for_view(
    view: QWebEngineView,
    central_manager: object | None,
    *,
    register_services: bool = False,
    on_create_route: _t.Callable | None = None,
    on_remove_route: _t.Callable | None = None,
    on_message_to_dock: _t.Callable[[str, str], None] | None = None,
) -> WebChannelContext:
    channel = QWebChannel()
    bridge = get_bridge(central_manager)

    services: dict[str, QObject] = {}

    if register_services:
        try:
            from .scene_service import SceneService
            from .ai_service import AIService
            from .scripting_service import ScriptingService
            from .project_service import ProjectService
            from .app_service import AppService

            scene_service = SceneService(bridge.scene_manager, bridge)
            ai_service = AIService(bridge)
            scripting_service = ScriptingService(bridge)
            project_service = ProjectService(scene_service, bridge)
            app_service = AppService(bridge)

            channel.registerObject("sceneService", scene_service)
            channel.registerObject("aiService", ai_service)
            channel.registerObject("scriptingService", scripting_service)
            channel.registerObject("projectService", project_service)
            channel.registerObject("appService", app_service)

            # 回填到 bridge，供 Bridge 槽函数委托
            try:
                bridge.scene_service = scene_service
                bridge.ai_service = ai_service
                bridge.scripting_service = scripting_service
                bridge.project_service = project_service
                bridge.app_service = app_service
            except Exception:
                pass

            # AppService -> UI 回调
            if on_create_route:
                app_service.create_route_requested.connect(on_create_route)
            else:
                try:
                    app_service.create_route_requested.connect(lambda a,b,c,d,e: bridge.create_route.emit(a,b,c,d,e))
                except Exception:
                    pass
            if on_remove_route:
                app_service.remove_route_requested.connect(on_remove_route)
            else:
                try:
                    app_service.remove_route_requested.connect(bridge.remove_route.emit)
                except Exception:
                    pass
            if on_message_to_dock:
                app_service.message_to_dock_requested.connect(on_message_to_dock)
            elif central_manager is not None:
                try:
                    app_service.message_to_dock_requested.connect(lambda name, data: central_manager.send_json_to_dock(name, data))
                except Exception:
                    pass
            # 直接转发主窗口命令
            try:
                app_service.command_to_main_requested.connect(lambda name, data: bridge.command_to_main.emit(name, data))
            except Exception:
                pass

            # 服务信号 -> 旧桥接信号（后端用），前端不再需要 pybridge
            scene_service.actor_created.connect(lambda s: bridge.dock_event.emit("actorCreated", s))
            scene_service.scene_loaded.connect(lambda s: bridge.dock_event.emit("sceneLoaded", s))
            scene_service.scene_error.connect(lambda s: bridge.dock_event.emit("sceneError", s))
            project_service.scene_saved.connect(lambda s: bridge.dock_event.emit("sceneSaved", s))
            ai_service.ai_response.connect(bridge.ai_response.emit)

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

    return WebChannelContext(channel=channel, bridge=bridge, services=services)


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

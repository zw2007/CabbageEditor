import json

from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from .dock_widget import RouteDockWidget, DockCleanupWidget
from ..utils.central_manager import CentralManager
from ..utils.webchannel_helper import setup_webchannel_for_view, teardown_webchannel_for_view


def get_dock_area(position, floatposition, size):
    position_map = {
        "left": (Qt.DockWidgetArea.LeftDockWidgetArea, False, None),
        "right": (Qt.DockWidgetArea.RightDockWidgetArea, False, None),
        "top": (Qt.DockWidgetArea.TopDockWidgetArea, False, None),
        "bottom": (Qt.DockWidgetArea.BottomDockWidgetArea, False, None),
    }

    if position.lower() == "float":
        screen = QGuiApplication.primaryScreen()
        float_position_map = {
            "top_left": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().topLeft()),
            "bottom_left": (Qt.DockWidgetArea.AllDockWidgetAreas, True,
                            screen.geometry().bottomLeft() - QPoint(0, 200)),
            "top_right": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().topRight() - QPoint(150, 0)),
            "bottom_right": (Qt.DockWidgetArea.AllDockWidgetAreas, True,
                             screen.geometry().bottomRight() - QPoint(150, 200)),
            "center": (
                Qt.DockWidgetArea.AllDockWidgetAreas,
                True,
                screen.geometry().center() - QPoint(int((size or {}).get("width", 600)) // 2,
                                                    int((size or {}).get("height", 320)) // 2),
            ),
        }
        return float_position_map.get(floatposition.lower(),
                                      (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().topLeft()))

    return position_map.get(
        position.lower(), (Qt.DockWidgetArea.LeftDockWidgetArea, False, None)
    )


class BrowserWidget(QWebEngineView):
    def __init__(self, Main_Window, url: QUrl):
        super(BrowserWidget, self).__init__(Main_Window)
        # 不再使用 bridge/channel
        self.Main_Window = Main_Window
        self.central_manager = CentralManager()

        if hasattr(self.central_manager, "set_creator"):
            self.central_manager.set_creator(self.AddDockWidget)
        if hasattr(self.central_manager, "set_remover"):
            self.central_manager.set_remover(self.RemoveDockWidget)

        self._webchannel_ctx = None

        self.url = QUrl(url) if isinstance(url, str) else url

        self.setMinimumSize(1, 1)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.page().setBackgroundColor(QColor(Qt.GlobalColor.transparent))
        self.load(self.url)
        self.setContentsMargins(0, 0, 0, 0)

        self.setup_web_channel()

    def setup_web_channel(self):
        # 通过回调直接接 appService 信号
        self._webchannel_ctx = setup_webchannel_for_view(
            self,
            self.central_manager,
            register_services=True,
            on_create_route=self.AddDockWidget,
            on_remove_route=self.RemoveDockWidget,
            on_message_to_dock=lambda name, data: self.central_manager.send_json_to_dock(name, data),
            on_command_to_main=self.handle_command_to_main,
        )

    def AddDockWidget(self, routename, routepath, position, floatposition, size):
        if not routename or not routepath:
            print("错误：routename 和 routepath 不能为空")
            return
        browser = QWebEngineView()
        browser.is_main_browser = False
        dock_area, isFloat, pos = get_dock_area(position, floatposition, size)

        if self.central_manager.docks.get(routename):
            self.RemoveDockWidget(routename)
            del self.central_manager.docks[routename]
            return
        try:
            dock = RouteDockWidget(browser, routename, routepath, self.central_manager, self.Main_Window, isFloat)
            if isFloat:
                if size:
                    dock.resize(size.get("width"), size.get("height"))
                    dock.browser.resize(size.get("width"), size.get("height"))
                dock.setWindowFlags(dock.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                dock.move(pos)
                dock.show()
            else:
                self.Main_Window.addDockWidget(dock_area, dock)

        except Exception as e:
            print(f"添加停靠窗口失败: {str(e)}")
            browser.deleteLater()

    def RemoveDockWidget(self, routename):
        browser = self.central_manager.docks.get(routename)
        dock = self.central_manager.docks.get(routename)
        if dock:
            self.Main_Window.removeDockWidget(dock)
            DockCleanupWidget(browser, routename, self.central_manager)

    def handle_command_to_main(self, command_name, command_data):
        if command_name == "go_home":
            self.load(self.url)
            return

        if command_name == "input_event":
            try:
                _ = json.loads(command_data) if isinstance(command_data, str) else command_data
            except Exception:
                pass
            return
        return

    def closeEvent(self, event):
        try:

            if getattr(self, "_webchannel_ctx", None):
                teardown_webchannel_for_view(self, self._webchannel_ctx)
                self._webchannel_ctx = None
        finally:
            super().closeEvent(event)

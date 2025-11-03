import os
import sys

from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QApplication, QDockWidget, QWidget
from .browser_widget import BrowserWidget
from .custom_window import CustomWindow
from .render_widget import RenderWidget
from ..utils.static_components import url

# 兼容常量（避免某些静态分析器无法解析 Qt 枚举名）
NO_DOCK = getattr(Qt, 'NoDockWidgetArea', 0)
TOP = getattr(Qt, 'TopDockWidgetArea', 0x1)
BOTTOM = getattr(Qt, 'BottomDockWidgetArea', 0x2)
LEFT = getattr(Qt, 'LeftDockWidgetArea', 0x4)
RIGHT = getattr(Qt, 'RightDockWidgetArea', 0x8)
HORIZONTAL = getattr(Qt, 'Horizontal', 0x1)
VERTICAL = getattr(Qt, 'Vertical', 0x2)
WA_TRANSPARENT = getattr(Qt, 'WA_TransparentForMouseEvents', 0)


def configure_web_engine() -> None:
    profile = QWebEngineProfile.defaultProfile()
    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)

    try:
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        profile.setHttpCacheMaximumSize(0)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
    except Exception:
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        self.osd = None
        super(MainWindow, self).__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        self.setWindowTitle("CoronaEngine")
        configure_web_engine()

        # 仅负责界面布局，不再承载停靠逻辑
        self.render_widget = RenderWidget(self)
        self.setCentralWidget(self.render_widget)

        self.osd = CustomWindow(self)
        self.osd.resize(self.size())
        self.osd.move(self.geometry().x(), self.geometry().y())

        self.browser_widget = BrowserWidget(self.osd, url)
        self.osd.setCentralWidget(self.browser_widget)

        self.osd.show()

    def changeEvent(self, event) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowMinimized:
                if self.osd:
                    self.osd.hide()
            else:
                old_state = getattr(event, 'oldState', lambda: None)()
                if (self.windowState() in (Qt.WindowState.WindowNoState, Qt.WindowState.WindowMaximized)
                        and old_state == Qt.WindowState.WindowMinimized):
                    if self.osd:
                        p = self.mapToGlobal(QPoint(0, 0))
                        self.osd.move(p.x(), p.y())
                        self.osd.show()
        super(MainWindow, self).changeEvent(event)

    def moveEvent(self, event) -> None:
        x = int(event.pos().x() - event.oldPos().x())
        y = int(event.pos().y() - event.oldPos().y())
        if self.osd:
            self.osd.move(self.osd.pos().x() + x, self.osd.pos().y() + y)
        super(MainWindow, self).moveEvent(event)

    def reloadWidget(self) -> None:

        for dock in self.findChildren(QDockWidget):
            dock.setParent(None)

        for child in self.children():
            if isinstance(child, QWebEngineView):
                child.setParent(None)

        if self.browser_widget:
            self.browser_widget.setParent(None)

        self.browser_widget = BrowserWidget(self.osd, url)
        self.osd.setCentralWidget(self.browser_widget)

    def closeEvent(self, event) -> None:
        QApplication.instance().quit()
        event.accept()
        os._exit(0)

    def resizeEvent(self, event) -> None:
        if getattr(self, "osd", None) is not None:
            self.osd.resize(self.size())
        super(MainWindow, self).resizeEvent(event)


app = None
window = None


def init_app(argv=None):
    """Create QApplication and MainWindow if not already created. Returns (app, window)."""
    global app, window
    if app is None:
        app = QApplication(argv or sys.argv)
    if window is None:
        window = MainWindow()
    try:
        window.show()
    except Exception:
        pass
    return app, window


def get_app():
    return app


def get_window():
    return window

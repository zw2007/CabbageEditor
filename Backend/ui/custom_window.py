from typing import Optional

from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtWidgets import QMainWindow, QWidget


# 常量兼容（避免分析器对 Qt 枚举解析问题）
NO_DOCK = getattr(Qt, 'NoDockWidgetArea', 0)
TOP = getattr(Qt, 'TopDockWidgetArea', 0x1)
BOTTOM = getattr(Qt, 'BottomDockWidgetArea', 0x2)
LEFT = getattr(Qt, 'LeftDockWidgetArea', 0x4)
RIGHT = getattr(Qt, 'RightDockWidgetArea', 0x8)
HORIZONTAL = getattr(Qt, 'Horizontal', 0x1)
VERTICAL = getattr(Qt, 'Vertical', 0x2)
WA_TRANSPARENT = getattr(Qt, 'WA_TransparentForMouseEvents', 0)


class CustomWindow(QMainWindow):
    def __init__(self, parent: Optional[QMainWindow] = None):
        super(CustomWindow, self).__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")

        # 允许在该窗口内停靠（BrowserWidget、RouteDockWidget 都挂在此处）
        self.setDockNestingEnabled(True)

        # 停靠预览/检测区
        self._dock_preview_timer = QTimer(self)
        self._dock_preview_timer.setSingleShot(True)
        self._dock_preview_timer.setInterval(300)
        self._dock_preview_timer.timeout.connect(self._show_pending_preview)

        self._pending_dock_area = NO_DOCK
        self._current_dock_area = NO_DOCK
        self._placeholder_dock = None
        self._dock_margin = 50

        # 四个可视化检测区域（便于调试）
        self._top_zone = QWidget(self)
        self._top_zone.setStyleSheet("background-color: rgba(255, 0, 0, 50);")
        self._top_zone.setAttribute(WA_TRANSPARENT)
        self._top_zone.hide()

        self._bottom_zone = QWidget(self)
        self._bottom_zone.setStyleSheet("background-color: rgba(0, 255, 0, 50);")
        self._bottom_zone.setAttribute(WA_TRANSPARENT)
        self._bottom_zone.hide()

        self._left_zone = QWidget(self)
        self._left_zone.setStyleSheet("background-color: rgba(255, 255, 0, 50);")
        self._left_zone.setAttribute(WA_TRANSPARENT)
        self._left_zone.hide()

        self._right_zone = QWidget(self)
        self._right_zone.setStyleSheet("background-color: rgba(0, 255, 255, 50);")
        self._right_zone.setAttribute(WA_TRANSPARENT)
        self._right_zone.hide()

    # 供 DockDragBridge/H5 调用的 API --------------------
    def show_detection_zones(self, show):
        if show:
            self._top_zone.show()
            self._bottom_zone.show()
            self._left_zone.show()
            self._right_zone.show()
        else:
            self._top_zone.hide()
            self._bottom_zone.hide()
            self._left_zone.hide()
            self._right_zone.hide()

    def _show_pending_preview(self):
        area = self._pending_dock_area
        if area == NO_DOCK:
            return
        if self._placeholder_dock:
            self.removeDockWidget(self._placeholder_dock)
            self._placeholder_dock.deleteLater()
            self._placeholder_dock = None
        ph = self._create_placeholder_dock(area)
        self.addDockWidget(area, ph)
        if area in (LEFT, RIGHT):
            self.resizeDocks([ph], [self.width() // 4], HORIZONTAL)
        else:
            self.resizeDocks([ph], [self.height() // 4], VERTICAL)
        self._placeholder_dock = ph
        self._current_dock_area = area

    def _create_placeholder_dock(self, area):
        from PySide6.QtWidgets import QDockWidget
        ph = QDockWidget()
        ph.setAllowedAreas(NO_DOCK)
        ph.setTitleBarWidget(QWidget())
        w = QWidget()
        color_map = {
            TOP: "rgba(255, 0, 0, 100)",
            BOTTOM: "rgba(0, 255, 0, 100)",
            LEFT: "rgba(255, 255, 0, 100)",
            RIGHT: "rgba(0, 255, 255, 100)",
        }
        w.setStyleSheet("background-color: {};".format(color_map.get(area)))
        ph.setWidget(w)
        return ph

    def get_docking_area(self, global_pos):
        rect = self.geometry()
        m = self._dock_margin
        if not rect.contains(global_pos):
            return NO_DOCK
        top_rect = QRect(rect.left(), rect.top(), rect.width(), m)
        bottom_rect = QRect(rect.left(), rect.bottom() - m, rect.width(), m)
        left_rect = QRect(rect.left(), rect.top(), m, rect.height())
        right_rect = QRect(rect.right() - m, rect.top(), m, rect.height())
        if top_rect.contains(global_pos):
            return TOP
        if bottom_rect.contains(global_pos):
            return BOTTOM
        if left_rect.contains(global_pos):
            return LEFT
        if right_rect.contains(global_pos):
            return RIGHT
        return NO_DOCK

    def update_dock_preview(self, global_pos):
        new_area = self.get_docking_area(global_pos)
        if new_area == self._pending_dock_area:
            return self._current_dock_area
        self._dock_preview_timer.stop()
        self._pending_dock_area = new_area
        if self._placeholder_dock:
            self.removeDockWidget(self._placeholder_dock)
            self._placeholder_dock.deleteLater()
            self._placeholder_dock = None
            self._current_dock_area = NO_DOCK
        if new_area != NO_DOCK:
            self._dock_preview_timer.start()
        return self._current_dock_area

    def try_dock_widget(self, global_pos, dock=None):
        self._dock_preview_timer.stop()
        if self._placeholder_dock:
            self.removeDockWidget(self._placeholder_dock)
            self._placeholder_dock.deleteLater()
            self._placeholder_dock = None
        area = self.get_docking_area(global_pos)
        if area != NO_DOCK and dock is not None:
            try:
                self.addDockWidget(area, dock)
                dock.setFloating(False)
            except Exception:
                pass
        self._current_dock_area = NO_DOCK

    # 同步检测区几何 --------------------
    def resizeEvent(self, event):
        m = self._dock_margin
        self._top_zone.setGeometry(0, 0, self.width(), m)
        self._bottom_zone.setGeometry(0, self.height() - m, self.width(), m)
        self._left_zone.setGeometry(0, 0, m, self.height())
        self._right_zone.setGeometry(self.width() - m, 0, m, self.height())
        super(CustomWindow, self).resizeEvent(event)

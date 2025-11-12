from typing import Optional

from PySide6.QtCore import Qt, QRect, QTimer, QPoint
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
        # 拖拽状态与策略：仅在停留超时后显示占位；在释放时才停靠
        self._dragging_dock = None
        self._dock_on_release = True

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
    def set_dragging_dock(self, dock):
        self._dragging_dock = dock

    def show_detection_zones(self, show):
        # 去掉半透明预览区：始终隐藏检测条
        self._top_zone.hide()
        self._bottom_zone.hide()
        self._left_zone.hide()
        self._right_zone.hide()

    def _set_placeholder(self, area):
        # 清除旧的占位
        if self._placeholder_dock:
            try:
                self.removeDockWidget(self._placeholder_dock)
                self._placeholder_dock.deleteLater()
            except Exception:
                pass
            self._placeholder_dock = None
        # 创建新的占位
        if area != NO_DOCK:
            ph = self._create_placeholder_dock(area)
            try:
                self.addDockWidget(area, ph)
                if area in (LEFT, RIGHT):
                    self.resizeDocks([ph], [max(1, self.width() // 4)], HORIZONTAL)
                else:
                    self.resizeDocks([ph], [max(1, self.height() // 4)], VERTICAL)
                self._placeholder_dock = ph
            except Exception:
                try:
                    ph.deleteLater()
                except Exception:
                    pass
                self._placeholder_dock = None

    def _show_pending_preview(self):
        # 延迟到达：仅显示占位，不自动停靠
        if self._pending_dock_area != NO_DOCK:
            self._set_placeholder(self._pending_dock_area)
            # 标记当前占位区域；保留 pending，避免在同一区域内重复启动计时器
            self._current_dock_area = self._pending_dock_area

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
        # 使用全局坐标系的窗口矩形（兼容顶层/子窗口）
        top_left = self.mapToGlobal(QPoint(0, 0))
        rect = QRect(top_left.x(), top_left.y(), self.width(), self.height())
        m = self._dock_margin
        if not rect.contains(global_pos):
            return NO_DOCK
        # 去掉上下的检测区，仅保留左右边缘
        left_rect = QRect(rect.left(), rect.top(), m, rect.height())
        right_rect = QRect(rect.right() - m, rect.top(), m, rect.height())
        if left_rect.contains(global_pos):
            return LEFT
        if right_rect.contains(global_pos):
            return RIGHT
        return NO_DOCK

    def update_dock_preview(self, global_pos):
        """延迟创建/移除占位，并返回当前已显示的占位区域（NO_DOCK 表示无预览）。"""
        new_area = self.get_docking_area(global_pos)
        # 如果区域未变化，直接返回当前占位区域
        if new_area == self._pending_dock_area:
            return self._current_dock_area

        # 停止上一次等待
        self._dock_preview_timer.stop()
        self._pending_dock_area = new_area

        # 离开停靠区：移除占位并重置
        if new_area == NO_DOCK:
            if self._placeholder_dock:
                try:
                    self.removeDockWidget(self._placeholder_dock)
                    self._placeholder_dock.deleteLater()
                except Exception:
                    pass
                self._placeholder_dock = None
            self._current_dock_area = NO_DOCK
            return self._current_dock_area

        # 进入新停靠区：启动延迟计时器，计时结束后在 _show_pending_preview 中创建占位
        try:
            self._dock_preview_timer.start()
        except Exception:
            # 若计时器异常，直接降级为立即占位
            self._set_placeholder(new_area)
            self._current_dock_area = new_area
        return self._current_dock_area

    def try_dock_widget(self, global_pos, dock=None):
        # 释放时执行真实停靠（依据开关，当前开启）
        if not self._dock_on_release:
            # 清理占位并退出
            self._dock_preview_timer.stop()
            if self._placeholder_dock:
                try:
                    self.removeDockWidget(self._placeholder_dock)
                    self._placeholder_dock.deleteLater()
                except Exception:
                    pass
                self._placeholder_dock = None
            self._current_dock_area = NO_DOCK
            return
        # 完成停靠并清理占位
        self._dock_preview_timer.stop()
        area = self.get_docking_area(global_pos)
        if self._placeholder_dock:
            try:
                self.removeDockWidget(self._placeholder_dock)
                self._placeholder_dock.deleteLater()
            except Exception:
                pass
            self._placeholder_dock = None
        if area != NO_DOCK and dock is not None:
            try:
                self.addDockWidget(area, dock)
                dock.setFloating(False)
            except Exception:
                pass
        # 重置状态
        self._current_dock_area = NO_DOCK
        self._pending_dock_area = NO_DOCK

    # 同步检测区几何 --------------------
    def resizeEvent(self, event):
        m = self._dock_margin
        self._top_zone.setGeometry(0, 0, self.width(), m)
        self._bottom_zone.setGeometry(0, self.height() - m, self.width(), m)
        self._left_zone.setGeometry(0, 0, m, self.height())
        self._right_zone.setGeometry(self.width() - m, 0, m, self.height())
        super(CustomWindow, self).resizeEvent(event)

import json

from PySide6.QtCore import Qt, QTimer, QObject, Slot, QPoint
from PySide6.QtGui import QColor, QCursor, QGuiApplication
from PySide6.QtWidgets import QDockWidget, QWidget
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from ..utils.webchannel_helper import setup_webchannel_for_view, teardown_webchannel_for_view


class DockDragBridge(QObject):
    """Expose minimal drag hooks for H5 to control float/move and trigger docking preview."""
    def __init__(self, dock_widget, main_window, parent=None):
        super(DockDragBridge, self).__init__(parent)
        self._dock = dock_widget
        self._main = main_window
        self._drag_start_global = None
        self._orig_dock_global = None
        # resize state
        self._resize_dir = None
        self._resize_start_mouse = None
        self._resize_start_geom = None
        self._NO_DOCK = getattr(Qt, 'NoDockWidgetArea', 0)

    @Slot(int, int)
    def start_drag(self, x, y):
        try:
            if not self._dock.isFloating():
                self._dock.setFloating(True)
                self._dock.raise_()
            # 显示/隐藏检测区域（当前实现始终隐藏，但调用不影响）
            if hasattr(self._main, 'show_detection_zones'):
                self._main.show_detection_zones(True)
            # 标记正在拖拽的 dock，供延迟停靠使用
            if hasattr(self._main, 'set_dragging_dock'):
                try:
                    self._main.set_dragging_dock(self._dock)
                except Exception:
                    pass
            web = self._dock.widget()
            web_global = web.mapToGlobal(QPoint(0, 0)) if web else self._dock.mapToGlobal(QPoint(0, 0))
            self._drag_start_global = web_global + QPoint(int(x), int(y))
            self._orig_dock_global = self._dock.mapToGlobal(QPoint(0, 0))
        except Exception:
            pass

    @Slot(int, int)
    def drag_move(self, x, y):
        # 若已不再浮动（可能已在计时器触发时自动停靠），停止移动
        if not self._dock.isFloating():
            return
        if self._drag_start_global is None or self._orig_dock_global is None:
            return
        try:
            current_global = QCursor.pos()
            # 更新预览/计时（延迟停靠）
            area = self._NO_DOCK
            if hasattr(self._main, 'update_dock_preview'):
                area = self._main.update_dock_preview(current_global)
            # 无占位预览时，窗口跟随鼠标移动
            if area == self._NO_DOCK:
                delta = current_global - self._drag_start_global
                new_global = self._orig_dock_global + delta
                self._dock.move(new_global)
        except Exception:
            pass

    @Slot()
    def end_drag(self):
        try:
            # 释放时不再强制停靠（除非开启 _dock_on_release），仅做清理
            if hasattr(self._main, 'try_dock_widget') and self._drag_start_global is not None:
                try:
                    self._main.try_dock_widget(QCursor.pos(), self._dock)
                except TypeError:
                    self._main.try_dock_widget(QCursor.pos())
        except Exception:
            pass
        finally:
            if hasattr(self._main, 'show_detection_zones'):
                self._main.show_detection_zones(False)
            if hasattr(self._main, 'set_dragging_dock'):
                try:
                    self._main.set_dragging_dock(None)
                except Exception:
                    pass
            self._drag_start_global = None
            self._orig_dock_global = None

    # ---- Resize path via bridge ----
    @Slot(str, int, int)
    def start_resize(self, direction, x, y):
        try:
            if not self._dock.isFloating():
                self._dock.setFloating(True)
                self._dock.raise_()
            self._resize_dir = (direction or '').lower()
            self._resize_start_mouse = QCursor.pos()
            self._resize_start_geom = self._dock.frameGeometry()
        except Exception:
            self._resize_dir = None
            self._resize_start_mouse = None
            self._resize_start_geom = None

    @Slot(int, int)
    def resize_move(self, x, y):
        if not self._resize_dir or self._resize_start_mouse is None or self._resize_start_geom is None:
            return
        try:
            current = QCursor.pos()
            dx = current.x() - self._resize_start_mouse.x()
            dy = current.y() - self._resize_start_mouse.y()

            # starting geometry
            gx = self._resize_start_geom.x()
            gy = self._resize_start_geom.y()
            gw = self._resize_start_geom.width()
            gh = self._resize_start_geom.height()

            new_x, new_y, new_w, new_h = gx, gy, gw, gh
            d = self._resize_dir
            if 'n' in d:
                new_y = gy + dy
                new_h = gh - dy
            if 's' in d:
                new_h = gh + dy
            if 'w' in d:
                new_x = gx + dx
                new_w = gw - dx
            if 'e' in d:
                new_w = gw + dx

            # min constraints
            min_w, min_h = 200, 160
            if new_w < min_w:
                if 'w' in d:
                    # adjust x so right edge stays
                    new_x = new_x - (min_w - new_w)
                new_w = min_w
            if new_h < min_h:
                if 'n' in d:
                    new_y = new_y - (min_h - new_h)
                new_h = min_h

            # clamp to primary screen (basic)
            screen = QGuiApplication.primaryScreen().availableGeometry()
            # right/bottom clamp by shrinking if necessary
            if new_x < screen.left():
                if 'w' in d:
                    overflow = screen.left() - new_x
                    new_x = screen.left()
                    new_w = max(min_w, new_w - overflow)
                else:
                    new_x = screen.left()
            if new_y < screen.top():
                if 'n' in d:
                    overflow = screen.top() - new_y
                    new_y = screen.top()
                    new_h = max(min_h, new_h - overflow)
                else:
                    new_y = screen.top()
            if new_x + new_w > screen.right():
                # shrink width
                new_w = max(min_w, screen.right() - new_x)
            if new_y + new_h > screen.bottom():
                new_h = max(min_h, screen.bottom() - new_y)

            self._dock.setGeometry(new_x, new_y, new_w, new_h)
        except Exception:
            pass

    @Slot()
    def end_resize(self):
        self._resize_dir = None
        self._resize_start_mouse = None
        self._resize_start_geom = None


class RouteDockWidget(QDockWidget):
    def __init__(self, browser, name, path, CentralManager, Main_Window, isFloat):
        super(RouteDockWidget, self).__init__(name, Main_Window)
        self.round_corner_stylesheet = None
        self.page = None
        self.Main_Window = Main_Window
        self.max_width = int(Main_Window.width() * 0.3)
        self.min_height = int(Main_Window.height() * 0.5)
        self.browser = browser
        self.isFloat = isFloat
        self.central_manager = CentralManager
        self.name = name
        self.worker_threads = []
        self.profile = None
        self._webchannel_ctx = None
        self.services = {}

        from PySide6.QtCore import QUrl
        from ..utils.static_components import url as base_url
        self.url = QUrl(base_url.toString())
        self.url.setFragment(path)

        self.setup_ui()
        self.setup_web_channel()
        self.connect_signals()

        if isFloat:
            self.setFloating(True)
            self.show()

    def setup_ui(self):
        self.setMinimumSize(1, 1)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.update_stylesheet()
        self.setMaximumWidth(self.max_width)
        self.setMinimumHeight(self.min_height)
        self.setTitleBarWidget(QWidget())
        self.setContentsMargins(0, 0, 0, 0)

        self.browser.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.browser.setStyleSheet("background: transparent;")
        self.browser.page().setBackgroundColor(QColor(Qt.GlobalColor.transparent))
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        try:
            self.profile = QWebEngineProfile(self)

            try:

                if hasattr(self.profile, "setOffTheRecord"):
                    self.profile.setOffTheRecord(True)
                self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
                self.profile.setHttpCacheMaximumSize(0)
                self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)

                try:
                    settings = self.profile.settings()
                    settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
                except Exception:
                    pass
            except Exception:
                pass
            self.page = QWebEnginePage(self.profile, self.browser)
            self.browser.setPage(self.page)

            try:
                self.page.setBackgroundColor(QColor(Qt.GlobalColor.transparent))
            except Exception:
                pass
        except Exception:
            self.profile = None
        # NOTE: 延后加载到 setup_web_channel 之后，确保先设置 QWebChannel
        # self.browser.load(self.url)

        # NOTE: 延后注册 loadFinished 注入，保证在设置 WebChannel 后绑定
        # try:
        #     self.browser.loadFinished.connect(lambda ok, name=self.name: self.browser.page().runJavaScript(
        #         "window.__dockRouteName = {};".format(json.dumps(name))))
        # except Exception:
        #     pass

        self.setWidget(self.browser)

    def update_stylesheet(self):
        self.round_corner_stylesheet = """
            QDockWidget {
                background: rgba(0, 0, 0, 0); 
                border: 8px solid rgba(100, 100, 100, 150);
                border-radius: 5px;
                padding: 4px;
            }
            QDockWidget[floating="true"] {
                border: 8px solid rgba(120, 120, 120, 200);
                padding: 4px;
            }
            QDockWidget::title {
                height: 0px;
            }
        """
        self.setStyleSheet(self.round_corner_stylesheet)

    def setup_web_channel(self):
        def _on_msg_to_dock(routename, json_data):
            if routename == self.name:
                self.send_message_to_dock(json_data)

        def _on_create_route(routename, routepath, position, floatposition, size):
            try:
                creator = getattr(self.central_manager, '_creator', None)
                if callable(creator):
                    creator(routename, routepath, position, floatposition, size)
                    return
                # 兜底：直接调用主窗口的 BrowserWidget
                bw = getattr(self.Main_Window, 'browser_widget', None)
                if bw and hasattr(bw, 'AddDockWidget'):
                    bw.AddDockWidget(routename, routepath, position, floatposition, size)
                else:
                    print('[WARN] 未找到 Dock 创建回流目标（CentralManager/browser_widget）')
            except Exception as e:
                print('[ERROR] _on_create_route 处理失败: {}'.format(e))

        def _on_remove_route(routename):
            try:
                remover = getattr(self.central_manager, '_remover', None)
                if callable(remover):
                    remover(routename)
                    return
                bw = getattr(self.Main_Window, 'browser_widget', None)
                if bw and hasattr(bw, 'RemoveDockWidget'):
                    bw.RemoveDockWidget(routename)
                else:
                    self.central_manager.delete_dock(routename)
            except Exception as e:
                print('[ERROR] _on_remove_route 处理失败: {}'.format(e))

        host_window = getattr(self.Main_Window, 'osd', self.Main_Window)
        drag_bridge = DockDragBridge(self, host_window, self)

        self._webchannel_ctx = setup_webchannel_for_view(
            self.browser,
            self.central_manager,
            register_services=True,
            on_create_route=_on_create_route,
            on_remove_route=_on_remove_route,
            on_message_to_dock=_on_msg_to_dock,
            extra_objects={"dockBridge": drag_bridge},
        )
        self.services = getattr(self._webchannel_ctx, 'services', {}) or {}

        # 确保在设置 WebChannel 之后再加载页面，这样前端能拿到 dockBridge
        try:
            self.browser.loadFinished.connect(lambda ok, name=self.name: self.browser.page().runJavaScript(
                "window.__dockRouteName = {};".format(json.dumps(name))))
        except Exception:
            pass
        self.browser.load(self.url)

        self.central_manager.register_dock(self.name, self)

    def connect_signals(self):
        ai_service = self.services.get("aiService")
        if ai_service is not None:
            try:
                ai_service.ai_response.connect(self.send_ai_message_to_js)
            except Exception:
                pass

        self.topLevelChanged.connect(self.handle_top_level_change)
        self.destroyed.connect(self.cleanup_resources)

    def dock_event(self, event_type, event_data):
        try:
            data_obj = json.loads(event_data) if isinstance(event_data, str) else (event_data or {})
            inner_event = data_obj.get("event")
            if inner_event:
                event_type = inner_event
            target = data_obj.get("routename")
            if target is not None and target != self.name:
                return
        except Exception:
            return
        if event_type == "drag" and self.isFloating():
            try:
                data = data_obj if isinstance(data_obj, dict) else {}
                current_pos = self.pos()
                new_x = current_pos.x() + int(data.get("deltaX", 0))
                new_y = current_pos.y() + int(data.get("deltaY", 0))
                self.move(new_x, new_y)
            except Exception as e:
                print("处理拖拽事件失败: {}".format(str(e)))
        elif event_type == "close":
            self.close()
        elif event_type == "float":
            try:
                data = data_obj if isinstance(data_obj, dict) else {}
                self.setFloating(bool(data.get("isFloating", False)))
                self.raise_()
            except Exception as e:
                print("处理float事件失败: {}".format(str(e)))
        elif event_type == "resize":
            try:
                data = data_obj if isinstance(data_obj, dict) else {}
                x = int(data.get("x"))
                y = int(data.get("y"))
                width = int(data.get("width"))
                height = int(data.get("height"))

                self.move(x, y)
                self.resize(max(200, width), max(200, height))

            except Exception as e:
                print("处理resize事件失败: {}".format(str(e)))

    def handle_top_level_change(self):
        if self.isFloating():
            self.setStyleSheet(self.round_corner_stylesheet)
            features = self.features()
            features |= QDockWidget.DockWidgetFeature.DockWidgetFloatable
            features |= QDockWidget.DockWidgetFeature.DockWidgetMovable
            features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
            self.setFeatures(features)
            self.setMaximumWidth(16777215)
            self.setMinimumHeight(1)
        else:
            self.setStyleSheet(self.round_corner_stylesheet)
            self.setMaximumWidth(self.max_width)
            self.setMinimumHeight(self.min_height)
            if hasattr(self, "browser"):
                self.browser.update()

    def send_message_to_dock(self, json_data):
        self.dock_event("dockData", json_data)

    def send_message_to_main(self, json_data):
        pass

    def send_ai_message_to_js(self, message):
        try:
            if not isinstance(message, str):
                message = str(message)
            try:
                json.loads(message)
                js_code = "window.receiveAIMessage({})".format(message)
            except Exception:
                js_code = "window.receiveAIMessage({})".format(json.dumps({'content': message}))

            QTimer.singleShot(0, lambda: self.browser.page().runJavaScript(js_code))
        except Exception as e:
            print("发送消息到JS失败: {}".format(str(e)))

    def cleanup_resources(self):
        try:
            if getattr(self, "_webchannel_ctx", None):
                teardown_webchannel_for_view(self.browser, self._webchannel_ctx)
                self._webchannel_ctx = None
            if hasattr(self, "page") and self.page:
                self.page.deleteLater()
                self.page = None
            try:
                self.central_manager.delete_dock(self.name)
            except Exception:
                pass
            try:
                if getattr(self, "profile", None) is not None:
                    try:
                        self.profile.clearHttpCache()
                    except Exception:
                        pass
                    self.profile.deleteLater()
                    self.profile = None
            except Exception:
                pass
            if hasattr(self, "browser"):
                self.browser.deleteLater()
                print("清理浏览器资源: {}".format(self.name))
        except Exception as e:
            print("资源清理异常: {}".format(str(e)))

    def closeEvent(self, event):
        try:
            for thread in self.worker_threads:
                thread.quit()
                thread.wait()
            self.worker_threads.clear()
        except Exception as e:
            print("关闭事件处理异常: {}".format(str(e)))
        super(RouteDockWidget, self).closeEvent(event)


class DockCleanupWidget(QWidget):
    def __init__(self, browser, name, central_manager):
        super(DockCleanupWidget, self).__init__()
        self.central_manager = central_manager
        self.browser = browser
        dock = self.central_manager.docks.get(name)

        if dock:
            print("[DEBUG] 开始删除 {}".format(name))
            dock.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

            def step1():
                if dock and dock.isWidgetType():
                    content = dock.widget()
                    if content:
                        print("[DEBUG] Step1 清理内容 {}".format(name))
                        content.hide()
                        try:
                            if content.page():
                                content.page().setWebChannel(None)
                        except RuntimeError:
                            pass
                        content.setParent(None)
                QTimer.singleShot(50, step2)

            def step2():
                try:
                    if dock and dock.isWidgetType() and dock.isVisible():
                        print("[DEBUG] Step2 删除dock {}".format(name))
                        dock.hide()
                        dock.setParent(None)
                        dock.deleteLater()
                except RuntimeError as e:
                    print("[WARN] 对象已提前删除: {}".format(str(e)))

                if name in self.central_manager.docks:
                    del self.central_manager.docks[name]

                QTimer.singleShot(50, step3)

            def step3():
                print("[DEBUG] Step3 最终确认 {}".format(name))

            QTimer.singleShot(0, step1)

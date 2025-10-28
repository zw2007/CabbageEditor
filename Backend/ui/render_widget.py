import os
from typing import Optional

from PySide6.QtCore import QRect, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ..utils.scene_manager import SceneManager


class RenderWidget(QWidget):
    geometry_changed = Signal(QRect)

    def __init__(self, Main_Window):
        super(RenderWidget, self).__init__()
        self.Main_Window = Main_Window

        self.setGeometry(0, 0, self.Main_Window.width(), self.Main_Window.height())
        self.setStyleSheet("QLabel {background-color: transparent;}")

        try:
            import CoronaEngine
            print("import CoronaEngine")
        except ImportError:
            from ..corona_engine_fallback import CoronaEngine

                                                                                    
        self.engine_scene = CoronaEngine.Scene(int(self.winId()), False)

                                                                                    
                                                                                              
        try:
            self.scene_wrapper = SceneManager().create_scene("mainscene", engine_scene=self.engine_scene)
        except Exception as e:
            print(f"Failed to register mainscene with SceneManager: {e}")
            self.scene_wrapper = None

                                                                                                
        if self.scene_wrapper is not None:
            try:
                self.scene_wrapper.set_camera(
                    [10.0, 10.0, 0.0], [-1.0, -1.0, -1.0], [0.0, 1.0, 0.0], 45.0
                )
            except Exception as e:
                print(f"Failed to set camera on scene_wrapper: {e}")
        else:
                                                               
            try:
                self.engine_scene.setCamera(
                    [10.0, 10.0, 0.0], [-1.0, -1.0, -1.0], [0.0, 1.0, 0.0], 45.0
                )
            except Exception:
                pass

        self.image_path = os.path.join(os.path.dirname(__file__), "background.png")
        self.pixmap: Optional[QPixmap] = None
        if self.image_path and os.path.exists(self.image_path):
            self.pixmap = QPixmap(self.image_path)
            self.update()
        else:
            print(f"警告: 背景图片路径不存在: {self.image_path}")

    def paintEvent(self, event) -> None:
        if self.pixmap:
            painter = QPainter(self)
            painter.drawPixmap(self.rect(), self.pixmap)

    def scene(self):
        return self.winId()
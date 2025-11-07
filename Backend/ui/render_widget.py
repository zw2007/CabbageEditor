import os
from typing import Optional

from PySide6.QtCore import QRect, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ..utils.engine_import import load_corona_engine
from ..utils.scene import Scene
from ..utils.camera import Camera

CoronaEngine = load_corona_engine()

class RenderWidget(QWidget):
    geometry_changed = Signal(QRect)

    def __init__(self, Main_Window):
        super(RenderWidget, self).__init__()
        self.Main_Window = Main_Window

        self.setGeometry(0, 0, self.Main_Window.width(), self.Main_Window.height())
        self.setStyleSheet("QLabel {background-color: transparent;}")

        # 创建场景（不再需要 winId 参数）
        self.scene = Scene(name="mainscene", light_field=False)

        # 创建相机
        try:
            self.camera = Camera(
                position=[10.0, 10.0, 0.0],
                forward=[-1.0, -1.0, -1.0],
                world_up=[0.0, 1.0, 0.0],
                fov=45.0,
                name="MainCamera"
            )

            # 设置渲染表面（绑定到窗口）
            self.camera.set_surface(int(self.winId()))

            # 将相机添加到场景
            self.scene.add_camera(self.camera)

        except Exception as e:
            print(f"Failed to create or setup camera: {e}")
            self.camera = None

    def scene(self):
        """返回场景对象"""
        return self.scene

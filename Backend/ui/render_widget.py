from PySide6.QtCore import QRect, Signal, Qt
from PySide6.QtWidgets import QWidget

from ..utils.engine_import import load_corona_engine
from ..utils.scene import Scene
from ..utils.camera import Camera
from ..utils.scene_manager import SceneManager  # 新增导入

CoronaEngine = load_corona_engine()

class RenderWidget(QWidget):
    geometry_changed = Signal(QRect)

    def __init__(self, Main_Window):
        super(RenderWidget, self).__init__()
        self.Main_Window = Main_Window

        self.setGeometry(0, 0, self.Main_Window.width(), self.Main_Window.height())
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #282C34;")

        # 使用 SceneManager 创建/获取场景
        self.scene_manager = SceneManager()  # 单例获取
        self.scene = self.scene_manager.create_scene("MainScene", light_field=False)

        # 创建相机并加入场景
        try:
            self.camera = Camera(
                position=[10.0, 10.0, 0.0],
                forward=[-1.0, -1.0, -1.0],
                world_up=[0.0, 1.0, 0.0],
                fov=45.0,
                name="MainCamera"
            )
            self.camera.set_surface(int(self.winId()))
            self.scene.add_camera(self.camera)
        except Exception as e:
            print(f"[RenderWidget] Failed to create or setup camera: {e}")
            self.camera = None

    def get_scene(self) -> Scene:
        """返回当前渲染使用的场景对象"""
        return self.scene

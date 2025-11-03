from __future__ import annotations
import json
from PySide6.QtCore import QObject, Signal, Slot
from Backend.utils.scene_manager import SceneManager


class SceneService(QObject):
    scene_error = Signal(str)
    actor_created = Signal(str)
    scene_loaded = Signal(str)

    def __init__(self, scene_manager: SceneManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.scene_manager = scene_manager

    @Slot(str, str)
    def create_actor(self, scene_name: str, obj_path: str) -> None:
        scene = self.scene_manager.get_scene(scene_name)
        if not scene:
            print(f"场景 '{scene_name}' 不存在，无法创建角色")
            return
        actor_data = scene.add_actor(obj_path)
        try:
            self.actor_created.emit(json.dumps({"name": actor_data["name"], "path": obj_path}))
        except Exception:
            pass
        print("角色创建成功:", actor_data["name"])

    @Slot(str)
    def create_scene(self, data: str) -> None:
        try:
            scene_name = json.loads(data).get("sceneName")
        except Exception:
            scene_name = None
        if not scene_name:
            print("场景名为空")
            return
        self.scene_manager.create_scene(scene_name)
        print("场景创建成功:", scene_name)

    @Slot(str, str)
    def remove_actor(self, scene_name: str, actor_name: str) -> None:
        scene = self.scene_manager.get_scene(scene_name)
        if not scene:
            print(f"场景 '{scene_name}' 不存在，无法删除角色")
            return
        actor = scene.get_actor(actor_name)
        if not actor:
            print(f"角色 '{actor_name}' 不存在，无法删除")
            return
        scene.remove_actor(actor_name)
        print(f"角色 '{actor_name}' 已从场景 '{scene_name}' 中删除")

    @Slot(str)
    def actor_operation(self, data: str) -> None:
        try:
            actor_data = json.loads(data)
            scene_name = actor_data.get("sceneName")
            actor_name = actor_data.get("actorName")
            operation = actor_data.get("Operation")
            x, y, z = map(float, [actor_data.get("x", 0.0), actor_data.get("y", 0.0), actor_data.get("z", 0.0)])
            scene = self.scene_manager.get_scene(scene_name)
            if not scene:
                print(f"场景 '{scene_name}' 不存在，无法操作角色")
                return
            actor = scene.get_actor(actor_name)
            if not actor:
                print(f"角色 '{actor_name}' 不存在，无法操作")
                return
            if operation == "Scale":
                actor.scale([x, y, z])
            elif operation == "Move":
                actor.move([x, y, z])
            elif operation == "Rotate":
                actor.rotate([x, y, z])
        except Exception as e:
            print(f"Actor transform error: {str(e)}")

    @Slot(str)
    def camera_move(self, data: str) -> None:
        try:
            move_data = json.loads(data)
            scene_name = move_data.get("sceneName", "scene1")
            position = move_data.get("position", [0.0, 5.0, 10.0])
            forward = move_data.get("forward", [0.0, 1.5, 0.0])
            up = move_data.get("up", [0.0, -1.0, 0.0])
            fov = float(move_data.get("fov", 45.0))
            scene = self.scene_manager.get_scene(scene_name)
            if scene is None:
                print(f"场景 '{scene_name}' 不存在，无法设置相机")
                return
            scene.set_camera(position, forward, up, fov)
        except Exception as e:
            print(f"摄像头移动错误: {str(e)}")

    @Slot(str)
    def sun_direction(self, data: str) -> None:
        try:
            sun_data = json.loads(data)
            scene_name = sun_data.get("sceneName", "scene1")
            px = float(sun_data.get("px", 1.0))
            py = float(sun_data.get("py", 1.0))
            pz = float(sun_data.get("pz", 1.0))
            direction = [px, py, pz]
            scene = self.scene_manager.get_scene(scene_name)
            if scene is None:
                print(f"场景 '{scene_name}' 不存在，无法设置太阳方向")
                return
            scene.set_sun_direction(direction)
        except Exception as e:
            try:
                self.scene_error.emit(json.dumps({"type": "error", "message": str(e)}))
            except Exception:
                pass


from __future__ import annotations
import json
from PySide6.QtCore import QObject, Signal, Slot
from Backend.utils.file_handle import FileHandler
from .scene import SceneService


class ProjectService(QObject):
    scene_saved = Signal(str)
    scene_loaded = Signal(str)

    def __init__(self, scene_service: SceneService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.scene_service = scene_service
        self.file_handler = FileHandler()

    @Slot(str, str)
    def open_file_dialog(self, scene_name: str, file_type: str = "model") -> None:
        scene = self.scene_service.scene_manager.get_scene(scene_name)
        if not scene:
            print(f"场景 {scene_name} 不存在，无法加载资源")
            return
        if file_type == "model":
            _, file_path = self.file_handler.open_file("选择模型文件", "3D模型文件 (*.obj *.fbx *.dae)")
            if file_path:
                try:
                    actor_data = scene.add_actor(file_path)
                    self.scene_service.actor_created.emit(json.dumps({"name": actor_data["name"], "path": file_path}))
                except Exception as e:
                    print(f"创建角色失败: {str(e)}")
        elif file_type == "scene":
            content, file_path = self.file_handler.open_file("选择场景文件", "场景文件 (*.json)")
            if file_path and content:
                try:
                    scene_data = json.loads(content)
                    actors = []
                    for actor_name in list(scene.list_actor_names()):
                        scene.remove_actor(actor_name)
                    for actor in scene_data.get("actors", []):
                        path = actor.get("path")
                        if path:
                            actor_data = scene.add_actor(path)
                            actors.append({"name": actor_data["name"], "path": path})
                    self.scene_loaded.emit(json.dumps({"actors": actors}))
                except Exception as e:
                    print(f"加载场景失败: {str(e)}")
                    self.scene_service.scene_error.emit(json.dumps({"type": "error", "message": str(e)}))

    @Slot(str)
    def scene_save(self, data: str) -> None:
        try:
            scene_data = json.loads(data)
            content = json.dumps(scene_data, indent=4)
            save_path = self.file_handler.save_file(content, "保存场景文件", "场景文件 (*.json)")
            status = {"status": "success", "filepath": save_path} if save_path else {"status": "error",
                                                                                     "filepath": save_path}
            self.scene_saved.emit(json.dumps(status))
        except Exception as e:
            print(f"[ERROR] 保存场景失败: {str(e)}")


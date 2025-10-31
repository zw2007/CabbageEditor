import json
import os
import time
import traceback

from PySide6.QtCore import QThread, Signal, Slot, QObject
from PySide6.QtWidgets import QApplication
from ..mcp_client import qa_one_sync
from .file_handle import FileHandler
from .static_components import root_dir
from .scene_manager import SceneManager
from .engine_import import load_corona_engine

CoronaEngine = load_corona_engine()

_bridge_singleton = None


def get_bridge(central_manager=None):
    global _bridge_singleton
    if _bridge_singleton is None:
        instance = Bridge(central_manager)
        _bridge_singleton = instance
    else:
        # 始终更新 central_manager 引用，避免 child 页面没有传导致 None
        if central_manager is not None:
            _bridge_singleton.central_manager = central_manager
    return _bridge_singleton


class WorkerThread(QThread):
    work_finished = Signal()
    result_ready = Signal(object)

    def __init__(self, func, *args, parent: QObject | None = None, **kwargs):
        super().__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result_ready.emit(result)
        except Exception as e:
            print(f"Worker thread error: {str(e)}")
        finally:
            self.work_finished.emit()


class Bridge(QObject):
    create_route = Signal(str, str, str, str, object)
    ai_message = Signal(str)
    remove_route = Signal(str)
    ai_response = Signal(str)
    dock_event = Signal(str, str)
    command_to_main = Signal(str, str)  # 前端页面通过 appService.send_command_to_main 发送，例如 input_event，BrowserWidget 注入到事件总线
    key_event = Signal(str)

           
    script_dir = os.path.join(root_dir, "CabbageEditor", "Backend", "script")
    saves_dir = os.path.join(root_dir, "CabbageEditor", "saves")
    os.makedirs(script_dir, exist_ok=True)
    os.makedirs(saves_dir, exist_ok=True)

    obj_dir = ""

    def __init__(self, central_manager=None):
        super().__init__()
        self.camera_position = [0.0, 5.0, 10.0]
        self.camera_forward = [0.0, 1.5, 0.0]
        self.central_manager = central_manager
                 
        self.scene_manager = SceneManager()
        self._workers: set[WorkerThread] = set()

                                  
    @Slot(str, str, str, str, str)
    def add_dock_widget(self, routename, routepath, position="left", floatposition="None", size=None):
        app_service = getattr(self, "app_service", None)
        if app_service is not None:
            try:
                size_str = size if isinstance(size, str) or size is None else json.dumps(size)
                app_service.add_dock_widget(routename, routepath, position, floatposition, size_str)
                return
            except Exception as e:
                print(f"[WARN] AppService.add_dock_widget 委托失败，回退旧路径: {e}")

        try:
            if isinstance(size, str):
                size = json.loads(size)
        except json.JSONDecodeError:
            size = None
        self.create_route.emit(routename, routepath, position, floatposition, size)

    @Slot(str)
    def remove_dock_widget(self, routename):
        app_service = getattr(self, "app_service", None)
        if app_service is not None:
            try:
                app_service.remove_dock_widget(routename)
                return
            except Exception as e:
                print(f"[WARN] AppService.remove_dock_widget 委托失败，回退旧路径: {e}")
        self.remove_route.emit(routename)

    @Slot(str, str)
    def send_message_to_dock(self, routename, json_data):
        app_service = getattr(self, "app_service", None)
        if app_service is not None:
            try:
                app_service.send_message_to_dock(routename, json_data)
                return
            except Exception as e:
                print(f"[WARN] AppService.send_message_to_dock 委托失败，回退旧路径: {e}")
        try:
            self.central_manager.send_json_to_dock(routename, json_data)
        except Exception as e:
            print(f"发送消息失败: {str(e)}")


    @Slot(str, str)
    def create_actor(self, scene_name, obj_path):
        scene_service = getattr(self, "scene_service", None)
        if scene_service is not None:
            return scene_service.create_actor(scene_name, obj_path)

        scene = self.scene_manager.get_scene(scene_name)
        if not scene:
            print(f"场景 '{scene_name}' 不存在，无法创建角色")
            return
        scene.add_actor(obj_path)

    @Slot(str)
    def create_scene(self, data):
        scene_service = getattr(self, "scene_service", None)
        if scene_service is not None:
            return scene_service.create_scene(data)

        try:
            scene_name = json.loads(data).get("sceneName")
        except Exception:
            scene_name = None
        if not scene_name:
            print("场景名为空")
            return
        self.scene_manager.create_scene(scene_name)

    @Slot(str, str)
    def remove_actor(self, sceneName, actorName):
        scene_service = getattr(self, "scene_service", None)
        if scene_service is not None:
            return scene_service.remove_actor(sceneName, actorName)

        scene = self.scene_manager.get_scene(sceneName)
        if not scene:
            print(f"场景 '{sceneName}' 不存在，无法删除角色")
            return
        if not scene.get_actor(actorName):
            print(f"角色 '{actorName}' 不存在，无法删除")
            return
        scene.remove_actor(actorName)

    @Slot(str)
    def actor_operation(self, data):
        scene_service = getattr(self, "scene_service", None)
        if scene_service is not None:
            return scene_service.actor_operation(data)

        try:
            Actor_data = json.loads(data)
            sceneName = Actor_data.get("sceneName")
            actorName = Actor_data.get("actorName")
            Operation = Actor_data.get("Operation")
            x, y, z = map(float, [Actor_data.get("x", 0.0), Actor_data.get("y", 0.0), Actor_data.get("z", 0.0)])

            scene = self.scene_manager.get_scene(sceneName)
            if not scene:
                return
            actor = scene.get_actor(actorName)
            if not actor:
                return
            if Operation == "Scale":
                actor.scale([x, y, z])
            elif Operation == "Move":
                actor.move([x, y, z])
            elif Operation == "Rotate":
                actor.rotate([x, y, z])
        except Exception:
            return

    @Slot(str)
    def camera_move(self, data):
        scene_service = getattr(self, "scene_service", None)
        if scene_service is not None:
            return scene_service.camera_move(data)
               
        try:
            move_data = json.loads(data)
            sceneName = move_data.get("sceneName", "scene1")
            position = move_data.get("position", [0.0, 5.0, 10.0])
            forward = move_data.get("forward", [0.0, 1.5, 0.0])
            up = move_data.get("up", [0.0, -1.0, 0.0])
            fov = float(move_data.get("fov", 45.0))
            scene = self.scene_manager.get_scene(sceneName)
            if scene is None:
                return
            scene.set_camera(position, forward, up, fov)
        except Exception:
            return

    @Slot(str)
    def sun_direction(self, data):
        scene_service = getattr(self, "scene_service", None)
        if scene_service is not None:
            return scene_service.sun_direction(data)

        try:
            sun_data = json.loads(data)
            sceneName = sun_data.get("sceneName", "scene1")
            px = float(sun_data.get("px", 1.0))
            py = float(sun_data.get("py", 1.0))
            pz = float(sun_data.get("pz", 1.0))
            direction = [px, py, pz]
            scene = self.scene_manager.get_scene(sceneName)
            if scene is None:
                return
            scene.set_sun_direction(direction)
        except Exception:
            return

                                    
    @Slot(str)
    def send_message_to_ai(self, ai_message: str):
        ai_service = getattr(self, "ai_service", None)
        if ai_service is not None:
            return ai_service.send_message_to_ai(ai_message)

        def ai_work() -> str:
            try:
                msg_data = json.loads(ai_message)
                query = msg_data.get("message", "")
                response_text = qa_one_sync(query=query)
                return json.dumps({"type": "ai_response", "content": response_text, "status": "success", "timestamp": int(time.time())})
            except Exception as e:
                return json.dumps({"type": "error", "content": str(e), "status": "error", "timestamp": int(time.time())})
        worker = WorkerThread(ai_work, parent=self)
        worker.result_ready.connect(self.ai_response.emit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self._workers.add(worker)
        worker.start()


    @Slot(str, str)
    def open_file_dialog(self, sceneName, file_type="model"):
        project_service = getattr(self, "project_service", None)
        if project_service is not None:
            return project_service.open_file_dialog(sceneName, file_type)

        file_handler = FileHandler()
        scene = self.scene_manager.get_scene(sceneName)
        if not scene:
            print(f"场景 {sceneName} 不存在，无法加载资源")
            return
        if file_type == "model":
            _, file_path = file_handler.open_file("选择模型文件", "3D模型文件 (*.obj *.fbx *.dae)")
            if file_path:
                try:
                    actor_data = scene.add_actor(file_path)
                    self.dock_event.emit("actorCreated", json.dumps({"name": actor_data["name"], "path": file_path}))
                except Exception as e:
                    print(f"创建角色失败: {str(e)}")
        elif file_type == "scene":
            content, file_path = file_handler.open_file("选择场景文件", "场景文件 (*.json)")
            if file_path and content:
                try:
                    data = json.loads(content)
                    for actor_name in list(scene.list_actor_names()):
                        scene.remove_actor(actor_name)
                    actors = []
                    for actor in data.get("actors", []):
                        path = actor.get("path")
                        if path:
                            actor_data = scene.add_actor(path)
                            actors.append({"name": actor_data["name"], "path": path})
                    self.dock_event.emit("sceneLoaded", json.dumps({"actors": actors}))
                except Exception as e:
                    self.dock_event.emit("sceneError", json.dumps({"type": "error", "message": str(e)}))

    @Slot(str)
    def scene_save(self, data):
        project_service = getattr(self, "project_service", None)
        if project_service is not None:
            return project_service.scene_save(data)

        try:
            scene_data = json.loads(data)
            file_handler = FileHandler()
            content = json.dumps(scene_data, indent=4)
            save_path = file_handler.save_file(content, "保存场景文件", "场景文件 (*.json)")
            if save_path:
                self.dock_event.emit("sceneSaved", json.dumps({"status": "success", "filepath": save_path}))
            else:
                self.dock_event.emit("sceneSaved", json.dumps({"status": "error", "filepath": save_path}))
        except Exception as e:
            print(f"[ERROR] 保存场景失败: {str(e)}")

# scene.py
from typing import Dict, List, Any
from .engine_object_factory import EngineObjectFactory


class Scene:
    """场景封装类，管理场景内的角色、相机、太阳方向等"""

    def __init__(self, name: str):
        self.name = name
        self.engine_scene = EngineObjectFactory.create_scene()  # 引擎场景实例
        self.actors: Dict[str, Dict[str, Any]] = {}  # 角色字典（name -> 角色数据）
        self.camera_position: List[float] = [0.0, 5.0, 10.0]
        self.camera_forward: List[float] = [0.0, 1.5, 0.0]
        self.camera_up: List[float] = [0.0, -1.0, 0.0]
        self.camera_fov: float = 45.0
        self.sun_direction: List[float] = [1.0, 1.0, 1.0]

    def add_actor(self, obj_path: str) -> Dict[str, Any]:
        """添加角色到场景"""
        actor_data = EngineObjectFactory.create_actor(obj_path)
        self.actors[actor_data["name"]] = actor_data
        return actor_data

    def remove_actor(self, actor_name: str) -> bool:
        """从场景移除角色"""
        if actor_name in self.actors:
            del self.actors[actor_name]
            return True
        return False

    def get_actor(self, actor_name: str) -> Dict[str, Any] | None:
        """获取场景中的角色"""
        return self.actors.get(actor_name)

    def set_camera(self, position: List[float], forward: List[float],
                   up: List[float], fov: float) -> None:
        """设置场景相机参数"""
        self.camera_position = position
        self.camera_forward = forward
        self.camera_up = up
        self.camera_fov = fov
        # 调用引擎接口更新相机
        if hasattr(self.engine_scene, 'setCamera'):
            self.engine_scene.setCamera(position, forward, up, fov)

    def set_sun_direction(self, direction: List[float]) -> None:
        """设置场景太阳方向"""
        self.sun_direction = direction
        # 调用引擎接口更新太阳
        if hasattr(self.engine_scene, 'setSunDirection'):
            self.engine_scene.setSunDirection(direction)
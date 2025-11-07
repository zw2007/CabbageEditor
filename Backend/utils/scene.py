from typing import Dict, List, Any, Optional
from .actor import Actor
from .camera import Camera
from .light import Light
import os


class Scene:
    """
    场景管理类，负责管理场景中的对象引用

    注意：Scene 只管理对象的引用，不负责对象的创建和销毁
    对象（Actor/Camera/Light）应该独立创建，通过 add_xxx 添加到场景
    """

    def __init__(self, name: str = "Scene", light_field: bool = False):
        """
        创建场景

        Args:
            name: 场景名称
            light_field: 是否使用光场
        """
        # 延迟导入避免循环依赖
        from .engine_object_factory import EngineObjectFactory

        self.name = name
        self.light_field = light_field

        # 创建引擎场景对象
        self.engine_scene = EngineObjectFactory.create_scene(light_field=light_field)

        # 对象引用列表（只存储引用，不负责生命周期）
        self._actors: List[Actor] = []
        self._cameras: List[Camera] = []
        self._lights: List[Light] = []

        # 场景配置
        self.sun_direction: List[float] = [0.0, -1.0, 0.0]

    def add_actor(self, actor: Actor) -> None:
        """
        添加 Actor 到场景（只添加引用，不创建对象）

        Args:
            actor: 已创建的 Actor 对象
        """
        if actor in self._actors:
            return  # 已存在，避免重复添加

        # 添加到本地列表
        self._actors.append(actor)
        print(self._actors)

        # 调用 C++ API：scene.add_actor(actor)
        if hasattr(self.engine_scene, 'add_actor'):
            self.engine_scene.add_actor(actor.engine_obj)

    def remove_actor(self, actor: Actor) -> bool:
        """
        从场景移除 Actor（只移除引用，不销毁对象）

        Args:
            actor: 要移除的 Actor 对象

        Returns:
            是否成功移除
        """
        if actor not in self._actors:
            return False

        # 从本地列表移除
        self._actors.remove(actor)

        # 调用 C++ API：scene.remove_actor(actor)
        if hasattr(self.engine_scene, 'remove_actor'):
            self.engine_scene.remove_actor(actor.engine_obj)

        return True

    def add_camera(self, camera: Camera) -> None:
        """
        添加 Camera 到场景（只添加引用，不创建对象）

        Args:
            camera: 已创建的 Camera 对象
        """
        if camera in self._cameras:
            return

        self._cameras.append(camera)

        if hasattr(self.engine_scene, 'add_camera'):
            self.engine_scene.add_camera(camera.engine_obj)

    def remove_camera(self, camera: Camera) -> bool:
        """
        从场景移除 Camera（只移除引用，不销毁对象）

        Args:
            camera: 要移除的 Camera 对象

        Returns:
            是否成功移除
        """
        if camera not in self._cameras:
            return False

        self._cameras.remove(camera)

        if hasattr(self.engine_scene, 'remove_camera'):
            self.engine_scene.remove_camera(camera.engine_obj)

        return True

    def add_light(self, light: Light) -> None:
        """
        添加 Light 到场景（只添加引用，不创建对象）

        Args:
            light: 已创建的 Light 对象
        """
        if light in self._lights:
            return

        self._lights.append(light)

        if hasattr(self.engine_scene, 'add_light'):
            self.engine_scene.add_light(light.engine_obj)

    def remove_light(self, light: Light) -> bool:
        """
        从场景移除 Light（只移除引用，不销毁对象）

        Args:
            light: 要移除的 Light 对象

        Returns:
            是否成功移除
        """
        if light not in self._lights:
            return False

        self._lights.remove(light)

        if hasattr(self.engine_scene, 'remove_light'):
            self.engine_scene.remove_light(light.engine_obj)

        return True

    def set_sun_direction(self, direction: List[float]) -> None:
        """
        设置太阳方向（平行光方向）

        Args:
            direction: 方向向量 [x, y, z]
        """
        self.sun_direction = direction

        if hasattr(self.engine_scene, 'set_sun_direction'):
            self.engine_scene.set_sun_direction(direction)

    # 查询方法
    def get_actors(self) -> List[Actor]:
        """获取场景中所有 Actor"""
        return self._actors.copy()

    def get_actor(self, key: Optional[Any]) -> Optional[Actor]:
        """获取单个 Actor。
        参数 key 支持：
        - str: 按名称匹配（actor.name）
        - int: 按索引（越界返回 None）
        - None: 返回 None（如需全部请用 get_actors）
        """
        if key is None:
            return None
        if isinstance(key, int):
            if 0 <= key < len(self._actors):
                return self._actors[key]
            return None
        if isinstance(key, str):
            for a in self._actors:
                if a.name == key:
                    return a
            return None
        # 不支持的类型
        return None

    def get_cameras(self) -> List[Camera]:
        """获取场景中所有 Camera"""
        return self._cameras.copy()

    def get_lights(self) -> List[Light]:
        """获取场景中所有 Light"""
        return self._lights.copy()

    def clear_actors(self) -> None:
        """清空所有 Actor 引用（不销毁对象）"""
        for actor in self._actors.copy():
            self.remove_actor(actor)

    def clear_cameras(self) -> None:
        """清空所有 Camera 引用（不销毁对象）"""
        for camera in self._cameras.copy():
            self.remove_camera(camera)

    def clear_lights(self) -> None:
        """清空所有 Light 引用（不销毁对象）"""
        for light in self._lights.copy():
            self.remove_light(light)

    def clear(self) -> None:
        """清空场景中所有对象引用（不销毁对象）"""
        self.clear_actors()
        self.clear_cameras()
        self.clear_lights()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式（用于序列化）

        Returns:
            包含场景数据的字典
        """
        return {
            "name": self.name,
            "light_field": self.light_field,
            "sun_direction": self.sun_direction,
            "actors": [actor.to_dict() for actor in self._actors],
            "cameras": [camera.to_dict() for camera in self._cameras],
            "lights": [light.to_dict() for light in self._lights],
        }

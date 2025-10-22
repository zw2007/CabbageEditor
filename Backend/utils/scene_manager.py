# scene_manager.py
from typing import Dict, Optional
from .scene import Scene


class SceneManager:
    """场景管理器（单例），管理所有场景的创建、查询、删除"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.scenes: Dict[str, Scene] = {}  # 场景名 -> Scene对象
        return cls._instance

    def create_scene(self, scene_name: str) -> Scene:
        """创建场景（若已存在则返回现有场景）"""
        if scene_name not in self.scenes:
            self.scenes[scene_name] = Scene(scene_name)
        return self.scenes[scene_name]

    def get_scene(self, scene_name: str) -> Optional[Scene]:
        """获取场景"""
        return self.scenes.get(scene_name)

    def delete_scene(self, scene_name: str) -> bool:
        """删除场景"""
        if scene_name in self.scenes:
            del self.scenes[scene_name]
            return True
        return False
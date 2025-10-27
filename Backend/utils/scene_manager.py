# scene_manager.py
from typing import Dict, Optional, Any
from .scene import Scene


class SceneManager:
    """场景管理器（单例），管理所有场景的创建、查询、删除"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # initialize scenes mapping on the singleton instance
            cls._instance.scenes = {}
        return cls._instance

    def create_scene(self, scene_name: str, engine_scene: Any = None) -> Scene:
        """创建场景（若已存在则返回现有场景）。可选注入 engine_scene 用于 RenderWidget。"""
        if scene_name not in self.scenes:
            scene = Scene(scene_name, engine_scene=engine_scene)
            self.scenes[scene_name] = scene
            # populate compatibility scene_dict if available
            try:
                from .static_components import scene_dict

                scene_dict[scene_name] = {"scene": scene.engine_scene, "actor_dict": {}}
            except Exception:
                pass
        return self.scenes[scene_name]

    def get_scene(self, scene_name: str) -> Optional[Scene]:
        """获取场景"""
        return self.scenes.get(scene_name)

    def delete_scene(self, scene_name: str) -> bool:
        """删除场景"""
        if scene_name in self.scenes:
            del self.scenes[scene_name]
            try:
                from .static_components import scene_dict

                if scene_name in scene_dict:
                    del scene_dict[scene_name]
            except Exception:
                pass
            return True
        return False

from typing import Dict, Any
import os


try:
    import CoronaEngine
    print("[EngineObjectFactory] 使用正式引擎 CoronaEngine")
except ImportError:
    try:
        from corona_engine_fallback import CoronaEngine
        print("[EngineObjectFactory] 使用 CoronaEngineFallback")
    except ImportError:
        print("[EngineObjectFactory] 未找到 CoronaEngine (需要 -DBUILD_CORONA_EDITOR=ON)")
        CoronaEngine = None


class EngineObjectFactory:
    """引擎对象工厂，统一创建Scene、Actor等核心对象"""

    @staticmethod
    def create_scene() -> Any:
        """创建场景引擎实例"""
        if not CoronaEngine:
            raise RuntimeError("CoronaEngine 未初始化，无法创建场景")
        return CoronaEngine.Scene()

    @staticmethod
    def create_actor(obj_path: str) -> Dict[str, Any]:
        """创建角色引擎实例及元数据"""
        if not CoronaEngine:
            raise RuntimeError("CoronaEngine 未初始化，无法创建角色")
        if not os.path.exists(obj_path):
            raise FileNotFoundError(f"角色文件不存在: {obj_path}")

        actor_obj = CoronaEngine.Actor(obj_path)
        return {
            "engine_obj": actor_obj,
            "path": obj_path,
            "name": os.path.basename(obj_path)
        }



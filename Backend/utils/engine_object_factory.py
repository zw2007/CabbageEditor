from typing import Any
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

from .actor import Actor


class EngineObjectFactory:
    """引擎对象工厂，统一创建Scene、Actor等核心对象"""

    @staticmethod
    def create_scene() -> Any:
        """创建场景引擎实例"""
        if not CoronaEngine:
            raise RuntimeError("CoronaEngine 未初始化，无法创建场景")
        return CoronaEngine.Scene()

    @staticmethod
    def create_actor(engine_scene: Any, obj_path: str) -> Actor:
        """在给定的 engine_scene 中创建 actor 并返回 Actor wrapper

        The C++ engine (nanobind) should expose a constructor or factory that accepts
        (scene, path) or (path) — try both forms for compatibility with fallback.
        """
        if not CoronaEngine:
            raise RuntimeError("CoronaEngine 未初始化，无法创建角色")
        if not os.path.exists(obj_path):
            raise FileNotFoundError(f"角色文件不存在: {obj_path}")

        # Try engine API that accepts scene first
        try:
            actor_obj = CoronaEngine.Actor(engine_scene, obj_path)
        except Exception:
            # Fallback: try constructor with single arg
            try:
                actor_obj = CoronaEngine.Actor(obj_path)
            except Exception as e:
                raise RuntimeError(f"无法创建引擎Actor: {e}")

        return Actor(actor_obj, obj_path)

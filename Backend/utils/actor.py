from typing import Any, Dict
import os

from .engine_import import load_corona_engine

CoronaEngine = load_corona_engine()


class Actor:
    """
    Actor 包装类，代表场景中的一个可渲染对象

    使用方式：
        actor = Actor("path/to/model.obj")
        scene.add_actor(actor)
    """

    def __init__(self, path: str):
        """
        创建 Actor 对象

        Args:
            path: 模型文件路径
        """
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化")

        if not os.path.exists(path):
            raise FileNotFoundError(f"模型文件不存在: {path}")

        # 调用 C++ API: CoronaEngine.Actor(path)
        ActorCtor = getattr(CoronaEngine, 'Actor', None)
        if ActorCtor is None:
            raise RuntimeError("CoronaEngine 未提供 Actor 构造器")

        self.engine_obj = ActorCtor(path)
        self.path = path
        self.name = os.path.basename(path)

    def scale(self, v):
        """缩放 Actor"""
        try:
            self.engine_obj.scale(v)
        except Exception as e:
            raise RuntimeError(f"Actor.scale 失败: {e}") from e

    def move(self, v):
        """移动 Actor"""
        try:
            self.engine_obj.move(v)
        except Exception as e:
            raise RuntimeError(f"Actor.move 失败: {e}") from e

    def rotate(self, v):
        """旋转 Actor"""
        try:
            self.engine_obj.rotate(v)
        except Exception as e:
            raise RuntimeError(f"Actor.rotate 失败: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "name": self.name,
            "path": self.path,
            "engine_obj": self.engine_obj,
        }

    def __repr__(self):
        return f"Actor(name={self.name}, path={self.path})"

    def to_dict(self) -> Dict[str, Any]:
        """Compatibility helper that returns a dict similar to the old structure.
        Keys: name, path, engine_obj (or 'actor' in some callers).
        """
        return {
            'name': self.name,
            'path': self.path,
            'engine_obj': self.engine_obj,
            'actor': self.engine_obj,
        }

    def __repr__(self) -> str:
        return f"<Actor name={self.name} path={self.path} engine_obj={repr(self.engine_obj)}>"

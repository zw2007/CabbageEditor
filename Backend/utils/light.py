from typing import Any, Dict, List

from .engine_import import load_corona_engine

CoronaEngine = load_corona_engine()


class Light:
    """
    Light 包装类，代表场景中的光源

    使用方式：
        light = Light()
        scene.add_light(light)
    """

    def __init__(self, name: str = "Light"):
        """
        创建 Light 对象

        Args:
            name: 灯光名称
        """
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化")

        # 调用 C++ API: CoronaEngine.Light()
        LightCtor = getattr(CoronaEngine, 'Light', None)
        if LightCtor is None:
            raise RuntimeError("CoronaEngine 未提供 Light 构造器")

        self.engine_obj = LightCtor()
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            'name': self.name,
            'engine_obj': self.engine_obj,
        }

    def __repr__(self):
        return f"Light(name={self.name})"


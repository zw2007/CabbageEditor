from typing import Any, Dict, List

try:
    import CoronaEngine
except ImportError:
    from ..corona_engine_fallback import CoronaEngine


class Camera:
    def __init__(self, engine_obj: Any, name: str = "Camera"):
        self.engine_obj = engine_obj
        self.name = name

    def set_transform(self, position: List[float], forward: List[float], up: List[float], fov: float):
        """Set camera transform and fov. Delegates to engine if possible."""
        try:
            if hasattr(self.engine_obj, 'setTransform'):
                self.engine_obj.setTransform(position, forward, up, fov)
            elif hasattr(self.engine_obj, 'set_transform'):
                self.engine_obj.set_transform(position, forward, up, fov)
        except Exception:

            pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'camera': self.engine_obj,
        }

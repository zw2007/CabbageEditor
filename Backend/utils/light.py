from typing import Any, Dict, List

try:
    import CoronaEngine
except ImportError:
    from ..corona_engine_fallback import CoronaEngine


class Light:
    def __init__(self, engine_obj: Any, name: str = "Light"):
        self.engine_obj = engine_obj
        self.name = name

    def set_direction(self, direction: List[float]):
        try:
            if hasattr(self.engine_obj, 'setDirection'):
                self.engine_obj.setDirection(direction)
            elif hasattr(self.engine_obj, 'set_direction'):
                self.engine_obj.set_direction(direction)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'light': self.engine_obj,
        }

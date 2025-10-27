from typing import Any, Dict
import os

try:
    import CoronaEngine
except Exception:
    from corona_engine_fallback import CoronaEngine


class Actor:
    """Wrapper around an engine actor object.
    Exposes .engine_obj, .path, .name and convenience methods that delegate to CoronaEngine when available.
    """

    def __init__(self, engine_obj: Any, path: str):
        self.engine_obj = engine_obj
        self.path = path
        self.name = os.path.basename(path)

    def scale(self, v):
        try:
            if CoronaEngine and hasattr(CoronaEngine, 'Actor'):
                CoronaEngine.Actor.scale(self.engine_obj, v)
            elif hasattr(self.engine_obj, 'scale'):
                self.engine_obj.scale(v)
        except Exception:
            # swallow; caller may log
            raise

    def move(self, v):
        try:
            if CoronaEngine and hasattr(CoronaEngine, 'Actor'):
                CoronaEngine.Actor.move(self.engine_obj, v)
            elif hasattr(self.engine_obj, 'move'):
                self.engine_obj.move(v)
        except Exception:
            raise

    def rotate(self, v):
        try:
            if CoronaEngine and hasattr(CoronaEngine, 'Actor'):
                CoronaEngine.Actor.rotate(self.engine_obj, v)
            elif hasattr(self.engine_obj, 'rotate'):
                self.engine_obj.rotate(v)
        except Exception:
            raise

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


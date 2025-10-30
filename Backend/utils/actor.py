from typing import Any, Dict
import os

from .engine_import import load_corona_engine

CoronaEngine = load_corona_engine()


class Actor:
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

    def delete(self) -> bool:
        try:

            if CoronaEngine and hasattr(CoronaEngine, 'Actor') and hasattr(CoronaEngine.Actor, 'delete'):
                CoronaEngine.Actor.delete(self.engine_obj)
                return True

            if hasattr(self.engine_obj, 'delete'):
                self.engine_obj.delete()
                return True
        except Exception:
            return False
        return False

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

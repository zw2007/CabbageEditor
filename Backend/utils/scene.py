# scene.py
from typing import Dict, List, Any, Optional
from .engine_object_factory import EngineObjectFactory
from .actor import Actor


class Scene:
    """场景封装类，优先直接使用 C++ 引擎层的数据（ECS）作为单一数据源；
    仅在引擎不支持查询时保留一个最小的 Python 侧 registry（只保存 Actor wrapper 引用）
    """

    def __init__(self, name: str, engine_scene: Any = None):
        self.name = name
        # allow injection of an existing engine scene (RenderWidget needs this)
        if engine_scene is not None:
            self.engine_scene = engine_scene
        else:
            self.engine_scene = EngineObjectFactory.create_scene()  # 引擎场景实例
        # lightweight registry used only if engine doesn't provide listing APIs
        self._actor_registry: Dict[str, Actor] = {}
        self.camera_position: List[float] = [0.0, 5.0, 10.0]
        self.camera_forward: List[float] = [0.0, 1.5, 0.0]
        self.camera_up: List[float] = [0.0, -1.0, 0.0]
        self.camera_fov: float = 45.0
        self.sun_direction: List[float] = [1.0, 1.0, 1.0]

    # --- Actor management (prefer engine-side operations) ---
    def add_actor(self, obj_path: str) -> Dict[str, Any]:
        """在引擎 scene 中创建 actor，并返回兼容的 dict（name/path/engine_obj）。
        不在 Python 再做完整数据复制；若引擎无法列举 actor，我们会把 wrapper 保存在最小 registry 以便后续引用。
        """
        actor = EngineObjectFactory.create_actor(self.engine_scene, obj_path)

        # try to determine name from wrapper
        name = getattr(actor, 'name', None) or getattr(actor.engine_obj, 'name', None) or obj_path.split(os.sep)[-1]

        # if engine does not provide listing, keep minimal registry for lookup
        if not self._engine_supports_listing():
            self._actor_registry[name] = actor

        # update compatibility scene_dict entry if present
        try:
            from .static_components import scene_dict

            if self.name not in scene_dict:
                scene_dict[self.name] = {"scene": self.engine_scene, "actor_dict": {}}
            scene_dict[self.name]["actor_dict"][name] = actor.to_dict()
        except Exception:
            pass

        return actor.to_dict()

    def _engine_supports_listing(self) -> bool:
        """Detect if the engine scene exposes a way to enumerate actors. Try common API names."""
        eng = self.engine_scene
        if eng is None:
            return False
        for attr in ('listActors', 'list_actor_names', 'getActorNames', 'get_actor_names', 'actors', 'getActors'):
            if hasattr(eng, attr):
                return True
        return False

    def list_actor_names(self) -> List[str]:
        """Return list of actor names from engine if possible, else from minimal registry."""
        eng = self.engine_scene
        try:
            # Common engine APIs (try in order)
            if hasattr(eng, 'list_actor_names'):
                return list(eng.list_actor_names())
            if hasattr(eng, 'getActorNames'):
                return list(eng.getActorNames())
            if hasattr(eng, 'get_actor_names'):
                return list(eng.get_actor_names())
            if hasattr(eng, 'listActors'):
                # listActors might return objects with .name
                items = eng.listActors()
                names = []
                for it in items:
                    n = getattr(it, 'name', None) or getattr(it, 'get_name', lambda: None)()
                    if n:
                        names.append(n)
                return names
            if hasattr(eng, 'getActors'):
                items = eng.getActors()
                names = []
                for it in items:
                    n = getattr(it, 'name', None) or getattr(it, 'get_name', lambda: None)()
                    if n:
                        names.append(n)
                return names
        except Exception:
            pass

        # Fallback to registry kept by Python when engine lacks listing
        return list(self._actor_registry.keys())

    def get_actor(self, actor_name: str) -> Optional[Actor]:
        """Try to obtain an Actor wrapper for an existing actor in the engine.
        Prefer to wrap engine-provided actor objects; fallback to registry.
        """
        eng = self.engine_scene
        try:
            # Try engine-provided finders
            if hasattr(eng, 'getActor'):
                obj = eng.getActor(actor_name)
                if obj is not None:
                    return Actor(obj, getattr(obj, 'path', actor_name))
            if hasattr(eng, 'get_actor'):
                obj = eng.get_actor(actor_name)
                if obj is not None:
                    return Actor(obj, getattr(obj, 'path', actor_name))
            if hasattr(eng, 'findActor'):
                obj = eng.findActor(actor_name)
                if obj is not None:
                    return Actor(obj, getattr(obj, 'path', actor_name))
        except Exception:
            pass

        # Fallback: registry stored in Python when engine lacks listing
        return self._actor_registry.get(actor_name)

    def remove_actor(self, actor_name: str) -> bool:
        """Remove actor by name: if engine supports deletion, call it; otherwise remove from registry.
        Also update compatibility scene_dict.
        """
        eng = self.engine_scene
        removed = False
        try:
            # try engine-level removal APIs
            if hasattr(eng, 'removeActor'):
                removed = bool(eng.removeActor(actor_name))
            elif hasattr(eng, 'remove_actor'):
                removed = bool(eng.remove_actor(actor_name))
            else:
                # try to get actor object and call delete on it
                actor_obj = None
                if hasattr(eng, 'getActor'):
                    actor_obj = eng.getActor(actor_name)
                elif hasattr(eng, 'get_actor'):
                    actor_obj = eng.get_actor(actor_name)
                if actor_obj is not None and hasattr(actor_obj, 'delete'):
                    try:
                        actor_obj.delete()
                        removed = True
                    except Exception:
                        removed = False
        except Exception:
            removed = False

        # Fallback: remove from Python registry
        if not removed and actor_name in self._actor_registry:
            del self._actor_registry[actor_name]
            removed = True

        # Update compatibility scene_dict
        try:
            from .static_components import scene_dict

            if self.name in scene_dict and actor_name in scene_dict[self.name].get('actor_dict', {}):
                del scene_dict[self.name]['actor_dict'][actor_name]
        except Exception:
            pass

        return removed

    # camera & sun remain same
    def set_camera(self, position: List[float], forward: List[float],
                   up: List[float], fov: float) -> None:
        self.camera_position = position
        self.camera_forward = forward
        self.camera_up = up
        self.camera_fov = fov
        try:
            if hasattr(self.engine_scene, 'setCamera'):
                self.engine_scene.setCamera(position, forward, up, fov)
        except Exception:
            pass

    def set_sun_direction(self, direction: List[float]) -> None:
        self.sun_direction = direction
        try:
            if hasattr(self.engine_scene, 'setSunDirection'):
                self.engine_scene.setSunDirection(direction)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Compatibility view of the scene similar to previous scene_dict entries."""
        return {
            "scene": self.engine_scene,
            "actor_dict": {name: actor.to_dict() for name, actor in self._actor_registry.items()},
        }

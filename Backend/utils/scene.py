# scene.py
from typing import Dict, List, Any, Optional
from .engine_object_factory import EngineObjectFactory
from .actor import Actor
import os

class Scene:
    def __init__(self, name: str, engine_scene: Any = None):
        self.name = name
        # allow injection of an existing engine scene (RenderWidget needs this)
        if engine_scene is not None:
            self.engine_scene = engine_scene
        else:
            self.engine_scene = EngineObjectFactory.create_scene()  # 引擎场景实例
        self._actor_registry: Dict[str, Actor] = {}
        # camera / light wrappers (created lazily via factory)
        self._camera: Optional[Any] = None
        self._light: Optional[Any] = None

        self.camera_position: List[float] = [0.0, 5.0, 10.0]
        self.camera_forward: List[float] = [0.0, 1.5, 0.0]
        self.camera_up: List[float] = [0.0, -1.0, 0.0]
        self.camera_fov: float = 45.0
        self.sun_direction: List[float] = [1.0, 1.0, 1.0]

    # --- Actor management (prefer engine-side operations) ---
    def add_actor(self, obj_path: str) -> Dict[str, Any]:
        """在引擎 scene 中创建 actor，并返回兼容的 dict（name/path/engine_obj）。
        EngineObjectFactory.create_actor 已经实现了尝试复用已存在 engine actor 的逻辑。
        """
        actor = EngineObjectFactory.create_actor(self.engine_scene, obj_path)
        # prefer wrapper name if present
        name = getattr(actor, 'name', None) or getattr(actor.engine_obj, 'name', None) or os.path.basename(obj_path)

        if not self._engine_supports_listing():
            self._actor_registry[name] = actor
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
        Prefer to return a cached wrapper from EngineObjectFactory when possible.
        """
        eng = self.engine_scene
        try:
            # Try engine-provided finders to obtain the raw engine object
            obj = None
            try:
                if hasattr(eng, 'getActor'):
                    obj = eng.getActor(actor_name)
                elif hasattr(eng, 'get_actor'):
                    obj = eng.get_actor(actor_name)
                elif hasattr(eng, 'findActor'):
                    obj = eng.findActor(actor_name)
            except Exception:
                obj = None

            if obj is not None:
                # check factory cache to reuse wrapper
                cache = getattr(EngineObjectFactory, '_actor_cache', None)
                if cache is not None and actor_name in cache:
                    return cache[actor_name]
                # otherwise create a transient wrapper (don't duplicate registry)
                return Actor(obj, getattr(obj, 'path', actor_name))
        except Exception:
            pass

        # Fallback: registry stored in Python when engine lacks listing
        return self._actor_registry.get(actor_name)

    def remove_actor(self, actor_name: str) -> bool:
        """Remove actor by name: try engine APIs first; if we have a wrapper, call its delete() to avoid
        duplicated deletion logic. Returns True if actor was removed.
        """
        eng = self.engine_scene
        removed = False

        # Prefer wrapper-based deletion if we have a wrapper in our registry or factory cache
        wrapper = self._actor_registry.get(actor_name)
        if wrapper is None:
            cache = getattr(EngineObjectFactory, '_actor_cache', None)
            if cache is not None and actor_name in cache:
                wrapper = cache[actor_name]

        if wrapper is not None:
            try:
                removed = wrapper.delete()
            except Exception:
                removed = False

        if not removed:
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

    # camera & sun remain same but backed by factory
    def ensure_camera(self):
        if self._camera is None:
            try:
                self._camera = EngineObjectFactory.create_camera(self.engine_scene)
            except Exception:
                self._camera = None
        return self._camera

    def ensure_light(self):
        if self._light is None:
            try:
                self._light = EngineObjectFactory.create_light(self.engine_scene)
            except Exception:
                self._light = None
        return self._light

    def set_camera(self, position: List[float], forward: List[float],
                   up: List[float], fov: float) -> None:
        self.camera_position = position
        self.camera_forward = forward
        self.camera_up = up
        self.camera_fov = fov
        cam = self.ensure_camera()
        try:
            if cam and hasattr(cam.engine_obj, 'setTransform'):
                cam.engine_obj.setTransform(position, forward, up, fov)
            elif self.engine_scene is not None and hasattr(self.engine_scene, 'setCamera'):
                self.engine_scene.setCamera(position, forward, up, fov)
        except Exception:
            pass

    def set_sun_direction(self, direction: List[float]) -> None:
        self.sun_direction = direction
        light = self.ensure_light()
        try:
            if light and hasattr(light.engine_obj, 'setDirection'):
                light.engine_obj.setDirection(direction)
            elif hasattr(self.engine_scene, 'setSunDirection'):
                self.engine_scene.setSunDirection(direction)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Compatibility view of the scene similar to previous scene_dict entries.
        Include camera/light wrappers when available.
        """
        actor_dict = {name: actor.to_dict() for name, actor in self._actor_registry.items()}
        cam = self._camera
        light = self._light
        cam_dict = cam.to_dict() if cam is not None else None
        light_dict = light.to_dict() if light is not None else None
        return {
            "scene": self.engine_scene,
            "actor_dict": actor_dict,
            "camera": cam_dict,
            "light": light_dict,
        }

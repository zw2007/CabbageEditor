from typing import Any
import os
import weakref

from .engine_import import load_corona_engine

CoronaEngine = load_corona_engine()
if CoronaEngine is None:
    print("[EngineObjectFactory] 未找到 CoronaEngine (需要 -DBUILD_CORONA_EDITOR=ON)")
else:
    print("[EngineObjectFactory] 使用 CoronaEngine / CoronaEngineFallback")

from .actor import Actor
from .camera import Camera
from .light import Light


class EngineObjectFactory:
    _actor_cache = weakref.WeakValueDictionary()
    _camera_cache = weakref.WeakValueDictionary()
    _light_cache = weakref.WeakValueDictionary()

    @staticmethod
    def create_scene() -> Any:
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化，无法创建场景")
        SceneCtor = getattr(CoronaEngine, 'Scene', None)
        if SceneCtor is None:
            raise RuntimeError("CoronaEngine 未提供 Scene 构造器")
        return SceneCtor()

    @staticmethod
    def _try_find_engine_actor(engine_scene: Any, name: str):

        try:
            if engine_scene is None:
                return None
            if hasattr(engine_scene, 'getActor'):
                return engine_scene.getActor(name)
            if hasattr(engine_scene, 'get_actor'):
                return engine_scene.get_actor(name)
            if hasattr(engine_scene, 'findActor'):
                return engine_scene.findActor(name)

            if hasattr(engine_scene, 'listActors'):
                items = engine_scene.listActors()
                for it in items:
                    n = getattr(it, 'name', None) or (hasattr(it, 'get_name') and it.get_name())
                    if n == name:
                        return it
        except Exception:
            return None
        return None

    @classmethod
    def create_actor(cls, engine_scene: Any, obj_path: str) -> Actor:
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化，无法创建角色")
        if not os.path.exists(obj_path):
            raise FileNotFoundError(f"角色文件不存在: {obj_path}")

        name = os.path.basename(obj_path)

        try:
            found = cls._try_find_engine_actor(engine_scene, name)
            if found is None:
                found = cls._try_find_engine_actor(engine_scene, obj_path)
            if found is not None:

                eng_name = getattr(found, 'name', None)
                if not eng_name and hasattr(found, 'get_name'):
                    try:
                        eng_name = found.get_name()
                    except Exception:
                        eng_name = None
                key = eng_name or os.path.basename(obj_path) or obj_path

                if key in cls._actor_cache:
                    return cls._actor_cache[key]
                wrapper = Actor(found, obj_path)
                wrapper.name = key
                cls._actor_cache[key] = wrapper
                return wrapper
        except Exception:
            pass

        ActorCtor = getattr(CoronaEngine, 'Actor', None)
        if ActorCtor is None:
            raise RuntimeError("CoronaEngine 未提供 Actor 构造器")
        try:
            actor_obj = ActorCtor(engine_scene, obj_path)
        except Exception:
            try:
                actor_obj = ActorCtor(obj_path)
            except Exception as e:
                raise RuntimeError(f"无法创建引擎Actor: {e}")

        wrapper = Actor(actor_obj, obj_path)

        eng_name = getattr(actor_obj, 'name', None)
        if not eng_name and hasattr(actor_obj, 'get_name'):
            try:
                eng_name = actor_obj.get_name()
            except Exception:
                eng_name = None
        key_name = eng_name or os.path.basename(obj_path) or obj_path
        wrapper.name = key_name
        cls._actor_cache[key_name] = wrapper
        return wrapper

    @classmethod
    def create_camera(cls, engine_scene: Any, name: str = "MainCamera") -> Camera:
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化，无法创建Camera")

        if name in cls._camera_cache:
            return cls._camera_cache[name]

        cam_obj = None
        try:
            if engine_scene is not None:
                if hasattr(engine_scene, 'getCamera'):
                    cam_obj = engine_scene.getCamera()
                elif hasattr(engine_scene, 'get_camera'):
                    cam_obj = engine_scene.get_camera()

            if cam_obj is None:
                CameraCtor = getattr(CoronaEngine, 'Camera', None)
                if CameraCtor is not None:
                    cam_obj = CameraCtor(engine_scene)
        except Exception:
            cam_obj = None

        if cam_obj is None:
            raise RuntimeError("无法创建或获取引擎Camera对象")

        wrapper = Camera(cam_obj, name)
        cls._camera_cache[name] = wrapper
        return wrapper

    @classmethod
    def create_light(cls, engine_scene: Any, name: str = "Sun") -> Light:
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化，无法创建Light")
        if name in cls._light_cache:
            return cls._light_cache[name]

        light_obj = None
        try:
            if engine_scene is not None and hasattr(engine_scene, 'getLight'):
                light_obj = engine_scene.getLight()
            if light_obj is None:
                LightCtor = getattr(CoronaEngine, 'Light', None)
                if LightCtor is not None:
                    light_obj = LightCtor(engine_scene)
        except Exception:
            light_obj = None

        if light_obj is None:
            raise RuntimeError("无法创建或获取引擎Light对象")

        wrapper = Light(light_obj, name)
        cls._light_cache[name] = wrapper
        return wrapper

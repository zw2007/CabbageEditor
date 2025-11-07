from typing import Any, Dict, List

from .engine_import import load_corona_engine

CoronaEngine = load_corona_engine()


class Camera:
    """
    Camera 包装类，代表场景中的相机

    使用方式：
        camera = Camera()
        camera.set_position([0, 5, 10])
        scene.add_camera(camera)
    """

    def __init__(self, position=None, forward=None, world_up=None, fov=None, name: str = "Camera"):
        """
        创建 Camera 对象

        Args:
            position: 相机位置 [x, y, z]，可选
            forward: 朝向向量 [x, y, z]，可选
            world_up: 世界向上向量 [x, y, z]，可选
            fov: 视场角（弧度），可选
            name: 相机名称
        """
        if CoronaEngine is None:
            raise RuntimeError("CoronaEngine 未初始化")

        # 调用 C++ API: CoronaEngine.Camera() 或 CoronaEngine.Camera(position, forward, world_up, fov)
        CameraCtor = getattr(CoronaEngine, 'Camera', None)
        if CameraCtor is None:
            raise RuntimeError("CoronaEngine 未提供 Camera 构造器")

        if position is not None and forward is not None and world_up is not None and fov is not None:
            # 使用完整参数构造
            self.engine_obj = CameraCtor(position, forward, world_up, fov)
        else:
            # 使用默认构造
            self.engine_obj = CameraCtor()

        self.name = name

    def set_position(self, position: List[float]):
        """设置相机位置"""
        try:
            self.engine_obj.set_position(position)
        except Exception as e:
            raise RuntimeError(f"Camera.set_position 失败: {e}") from e

    def get_position(self) -> List[float]:
        """获取相机位置"""
        try:
            return self.engine_obj.get_position()
        except Exception as e:
            raise RuntimeError(f"Camera.get_position 失败: {e}") from e

    def set_forward(self, forward: List[float]):
        """设置相机朝向"""
        try:
            self.engine_obj.set_forward(forward)
        except Exception as e:
            raise RuntimeError(f"Camera.set_forward 失败: {e}") from e

    def get_forward(self) -> List[float]:
        """获取相机朝向"""
        try:
            return self.engine_obj.get_forward()
        except Exception as e:
            raise RuntimeError(f"Camera.get_forward 失败: {e}") from e

    def set_world_up(self, world_up: List[float]):
        """设置世界向上向量"""
        try:
            self.engine_obj.set_world_up(world_up)
        except Exception as e:
            raise RuntimeError(f"Camera.set_world_up 失败: {e}") from e

    def get_world_up(self) -> List[float]:
        """获取世界向上向量"""
        try:
            return self.engine_obj.get_world_up()
        except Exception as e:
            raise RuntimeError(f"Camera.get_world_up 失败: {e}") from e

    def set_fov(self, fov: float):
        """设置视场角"""
        try:
            self.engine_obj.set_fov(fov)
        except Exception as e:
            raise RuntimeError(f"Camera.set_fov 失败: {e}") from e

    def get_fov(self) -> float:
        """获取视场角"""
        try:
            return self.engine_obj.get_fov()
        except Exception as e:
            raise RuntimeError(f"Camera.get_fov 失败: {e}") from e

    def move(self, delta: List[float]):
        """相对移动相机"""
        try:
            self.engine_obj.move(delta)
        except Exception as e:
            raise RuntimeError(f"Camera.move 失败: {e}") from e

    def rotate(self, euler: List[float]):
        """旋转相机"""
        try:
            self.engine_obj.rotate(euler)
        except Exception as e:
            raise RuntimeError(f"Camera.rotate 失败: {e}") from e

    def look_at(self, position: List[float], forward: List[float]):
        """设置相机看向指定方向"""
        try:
            self.engine_obj.look_at(position, forward)
        except Exception as e:
            raise RuntimeError(f"Camera.look_at 失败: {e}") from e

    def set_surface(self, surface: int):
        """设置渲染表面"""
        try:
            self.engine_obj.set_surface(surface)
        except Exception as e:
            raise RuntimeError(f"Camera.set_surface 失败: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            'name': self.name,
            'engine_obj': self.engine_obj,
        }

    def __repr__(self):
        return f"Camera(name={self.name})"


class CoronaEngine():
    class Scene():
        def __init__(self, light_field=False):
            """
            创建场景

            Args:
                light_field (bool): 是否使用光场，默认 False
            """
            self.light_field = light_field
            return

        def set_sun_direction(self, direction):
            """
            设置太阳方向

            Args:
                direction (list[float, float, float]): 太阳方向向量 [x, y, z]
            """
            print(f"CoronaEngine.Scene.set_sun_direction({direction})")
            return True

        def add_actor(self, actor):
            """
            添加 Actor 到场景

            Args:
                actor (Actor): Actor 实例
            """
            print("CoronaEngine.Scene.add_actor")
            return True

        def add_light(self, light):
            """
            添加 Light 到场景

            Args:
                light (Light): Light 实例
            """
            print("CoronaEngine.Scene.add_light")
            return True

        def add_camera(self, camera):
            """
            添加 Camera 到场景

            Args:
                camera (Camera): Camera 实例
            """
            print("CoronaEngine.Scene.add_camera")
            return True

        def remove_actor(self, actor):
            """
            从场景移除 Actor

            Args:
                actor (Actor): Actor 实例
            """
            print("CoronaEngine.Scene.remove_actor")
            return True

        def remove_light(self, light):
            """
            从场景移除 Light

            Args:
                light (Light): Light 实例
            """
            print("CoronaEngine.Scene.remove_light")
            return True

        def remove_camera(self, camera):
            """
            从场景移除 Camera

            Args:
                camera (Camera): Camera 实例
            """
            print("CoronaEngine.Scene.remove_camera")
            return True

    class Actor():
        def __init__(self, path=""):
            """
            创建 Actor（模型实体）

            Args:
                path (str): 模型文件路径，默认为空字符串
            """
            self.path = path
            return

        def move(self, position):
            """
            移动 Actor 到指定位置

            Args:
                position (list[float, float, float]): 位置 [x, y, z]
            """
            print(f"CoronaEngine.Actor.move({position})")
            return True

        def rotate(self, euler):
            """
            旋转 Actor

            Args:
                euler (list[float, float, float]): 欧拉角 [x, y, z]（弧度）
            """
            print(f"CoronaEngine.Actor.rotate({euler})")
            return True

        def scale(self, size):
            """
            缩放 Actor

            Args:
                size (list[float, float, float]): 缩放比例 [x, y, z]
            """
            print(f"CoronaEngine.Actor.scale({size})")
            return True

    class Light():
        def __init__(self):
            """
            创建 Light（灯光）
            """
            return

    class Camera():
        def __init__(self, position=None, forward=None, world_up=None, fov=None):
            """
            创建 Camera（相机）

            Args:
                position (list[float, float, float], optional): 相机位置 [x, y, z]
                forward (list[float, float, float], optional): 朝向向量 [x, y, z]
                world_up (list[float, float, float], optional): 世界向上向量 [x, y, z]
                fov (float, optional): 视场角（弧度）
            """
            self._position = position or [0.0, 0.0, 5.0]
            self._forward = forward or [0.0, 0.0, -1.0]
            self._world_up = world_up or [0.0, 1.0, 0.0]
            self._fov = fov or 0.785398  # 45度
            return

        def set_surface(self, surface):
            """
            设置渲染表面

            Args:
                surface (int): 窗口 ID (uintptr_t)
            """
            print(f"CoronaEngine.Camera.set_surface({surface})")
            return True

        def set_position(self, position):
            """
            设置相机位置

            Args:
                position (list[float, float, float]): 位置 [x, y, z]
            """
            print(f"CoronaEngine.Camera.set_position({position})")
            self._position = position
            return True

        def get_position(self):
            """
            获取相机位置

            Returns:
                list[float, float, float]: 位置 [x, y, z]
            """
            print("CoronaEngine.Camera.get_position()")
            return self._position

        def set_forward(self, forward):
            """
            设置相机朝向

            Args:
                forward (list[float, float, float]): 朝向向量 [x, y, z]
            """
            print(f"CoronaEngine.Camera.set_forward({forward})")
            self._forward = forward
            return True

        def get_forward(self):
            """
            获取相机朝向

            Returns:
                list[float, float, float]: 朝向向量 [x, y, z]
            """
            print("CoronaEngine.Camera.get_forward()")
            return self._forward

        def set_world_up(self, world_up):
            """
            设置世界向上向量

            Args:
                world_up (list[float, float, float]): 向上向量 [x, y, z]
            """
            print(f"CoronaEngine.Camera.set_world_up({world_up})")
            self._world_up = world_up
            return True

        def get_world_up(self):
            """
            获取世界向上向量

            Returns:
                list[float, float, float]: 向上向量 [x, y, z]
            """
            print("CoronaEngine.Camera.get_world_up()")
            return self._world_up

        def set_fov(self, fov):
            """
            设置视场角

            Args:
                fov (float): 视场角（弧度）
            """
            print(f"CoronaEngine.Camera.set_fov({fov})")
            self._fov = fov
            return True

        def get_fov(self):
            """
            获取视场角

            Returns:
                float: 视场角（弧度）
            """
            print("CoronaEngine.Camera.get_fov()")
            return self._fov

        def move(self, delta):
            """
            相对移动相机

            Args:
                delta (list[float, float, float]): 移动增量 [x, y, z]
            """
            print(f"CoronaEngine.Camera.move({delta})")
            self._position = [self._position[i] + delta[i] for i in range(3)]
            return True

        def rotate(self, euler):
            """
            旋转相机

            Args:
                euler (list[float, float, float]): 欧拉角 [x, y, z]（弧度）
            """
            print(f"CoronaEngine.Camera.rotate({euler})")
            return True

        def look_at(self, position, forward):
            """
            设置相机看向指定方向

            Args:
                position (list[float, float, float]): 相机位置 [x, y, z]
                forward (list[float, float, float]): 朝向向量 [x, y, z]
            """
            print(f"CoronaEngine.Camera.look_at(position={position}, forward={forward})")
            self._position = position
            self._forward = forward
            return True

class CoronaEngine():
    class Scene():
        def __init__(self, lightField=None):
            self.lightField = lightField
            return

        def set_sun_direction(self, direction):
            print("CoronaEngine.setSunDirection")
            return True

        def add_actor(self, Actor):
            print("CoronaEngine.addActor")
            return True

        def add_light(self, Light):
            print("CoronaEngine.addLight")
            return True

        def add_camera(self, Camera):
            print("CoronaEngine.addCamera")
            return True

        def remove_actor(self, Actor):
            print("CoronaEngine.removeActor")
            return True

        def remove_light(self, Light):
            print("CoronaEngine.removeLight")
            return True

        def remove_camera(self, Camera):
            print("CoronaEngine.removeCamera")
            return True

    class Actor():
        def __init__(self, path=None):
            self.path = path
            return

        def move(self, position):
            print("CoronaEngine.moveActor")
            return True

        def rotate(self, rotate):
            print("CoronaEngine.rotateActor")
            return True

        def scale(self, scale):
            print("CoronaEngine.scaleActor")
            return True

    class Light():
        def __init__(self, type=None):
            self.type = type
            return

        def move(self, position):
            print("CoronaEngine.moveLight")
            return True

        def rotate(self, rotate):
            print("CoronaEngine.rotateLight")
            return True

        def set_intensity(self, intensity):
            print("CoronaEngine.setLightIntensity")
            return True

    class Camera():
        def __init__(self):
            return

        def set_surface(self, winId):
            print("CoronaEngine.setCameraSurface")
            return True

        def move(self, position):
            print("CoronaEngine.moveCamera")
            return True

        def rotate(self, rotate):
            print("CoronaEngine.rotateCamera")
            return True

        def set_fov(self, fov):
            print("CoronaEngine.setCameraFOV")
            return True

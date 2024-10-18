import pygame
import numpy as np
import weakref
import carla
from carla import ColorConverter as cc

class CameraManager(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.surfaces = [None, None, None, None]
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        self._camera_transforms = [
            carla.Transform(carla.Location(x=-1.0, z=1.5), carla.Rotation(yaw=180, pitch=0)),  # Rear camera
            carla.Transform(carla.Location(x=1.6, z=1.7)),  # Dashboard view
            carla.Transform(carla.Location(x=-0.5, y=-1.5, z=1.7), carla.Rotation(yaw=-130, pitch=0)),  # Left mirror
            carla.Transform(carla.Location(x=-0.5, y=1.5, z=1.7), carla.Rotation(yaw=130, pitch=0)),  # Right mirror
        ]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Rear Camera'],
            ['sensor.camera.rgb', cc.Raw, 'Dashboard Camera'],
            ['sensor.camera.rgb', cc.Raw, 'Left Mirror Camera'],
            ['sensor.camera.rgb', cc.Raw, 'Right Mirror Camera'],
        ]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for idx, item in enumerate(self.sensors):
            bp = bp_library.find(item[0])
            if idx == 1:
                # Dashboard Camera is larger
                bp.set_attribute('image_size_x', str(1000))
                bp.set_attribute('image_size_y', str(768))
            elif idx == 0:
                # Rear Camera (smaller, and different size)
                bp.set_attribute('image_size_x', str(200))
                bp.set_attribute('image_size_y', str(100))
            else:
                # Other cameras are also smaller
                bp.set_attribute('image_size_x', str(350))
                bp.set_attribute('image_size_y', str(200))

            item.append(bp)

        self.indices = [None, None, None, None]  # Track the current camera index

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.sensor.set_transform(self._camera_transforms[self.transform_index])

    def set_sensor(self, index, notify=True):
        for i in range(4):
            self.spawn_sensor(i)

    def spawn_sensor(self, index):
        if self.indices[index] is not None and self.sensors[index][0] == self.sensors[self.indices[index]][0]:
            return

        if self.surfaces[index] is not None:
            self.sensors[index][3].destroy()
            self.surfaces[index] = None

        self.sensors[index][3] = self._parent.get_world().spawn_actor(
            self.sensors[index][-1],
            self._camera_transforms[index],
            attach_to=self._parent,
        )

        weak_self = weakref.ref(self)
        self.sensors[index][3].listen(lambda image, idx=index: CameraManager._parse_image(weak_self, image, idx))

        self.indices[index] = index

    # def next_sensor(self):
    #     self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        #self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        # Dashboard view at the left-most corner
        dashboard_x = 0
        dashboard_y = 0
        if self.surfaces[1] is not None:
            display.blit(self.surfaces[1], (dashboard_x, dashboard_y))

        mirror_x = dashboard_x + self.surfaces[1].get_width() + 10  # X position for all mirrors next to the dashboard

        # Left Mirror on top
        if self.surfaces[2] is not None:
            left_mirror_y = dashboard_y  # Top-aligned with the dashboard
            display.blit(self.surfaces[2], (mirror_x, left_mirror_y))

        # Right Mirror below the Left Mirror
        if self.surfaces[3] is not None:
            right_mirror_y = left_mirror_y + self.surfaces[2].get_height() + 10
            display.blit(self.surfaces[3], (mirror_x, right_mirror_y))

        # Rear Camera below the Right Mirror
        if self.surfaces[0] is not None:
            rear_camera_y = right_mirror_y + self.surfaces[3].get_height() + 10
            display.blit(self.surfaces[0], (mirror_x, rear_camera_y))

    @staticmethod
    def _parse_image(weak_self, image, index):
        self = weak_self()
        if not self:
            return

        image.convert(self.sensors[index][1])
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surfaces[index] = pygame.surfarray.make_surface(array.swapaxes(0, 1))

        if self.recording:
            image.save_to_disk(f'_out/{index}_{image.frame:08d}')



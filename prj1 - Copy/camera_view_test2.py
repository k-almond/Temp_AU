import carla
import pygame
import numpy as np
import random


def main():
    pygame.init()
    display = pygame.display.set_mode((1600, 600))  # Window size, adjust as needed

    client = carla.Client('localhost', 2000)
    client.set_timeout(3.0)
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()

    vehicle_bp = blueprint_library.find('vehicle.audi.a2')
    spawn_points = world.get_map().get_spawn_points()
    vehicle = None
    for spawn_point in spawn_points:
        try:
            vehicle = world.spawn_actor(vehicle_bp, spawn_point)
            break
        except RuntimeError:
            continue

    if not vehicle:
        print("Failed to spawn vehicle.")
        return

    cam_bp = blueprint_library.find('sensor.camera.rgb')
    cam_bp.set_attribute('image_size_x', '800')
    cam_bp.set_attribute('image_size_y', '600')
    cam_bp.set_attribute('fov', '90')

    cam_transform_left = carla.Transform(carla.Location(x=0.5, y=-0.5, z=1.5), carla.Rotation(yaw=-45))
    cam_left = world.spawn_actor(cam_bp, cam_transform_left, attach_to=vehicle)

    cam_transform_right = carla.Transform(carla.Location(x=0.5, y=0.5, z=1.5), carla.Rotation(yaw=45))
    cam_right = world.spawn_actor(cam_bp, cam_transform_right, attach_to=vehicle)

    def parse_image(image):
        image.convert(carla.ColorConverter.RGB)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]  # Drop the alpha channel
        surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        return surface

    while True:
        image_left = cam_left.listen(lambda image: display.blit(parse_image(image), (0, 0)))
        image_right = cam_right.listen(lambda image: display.blit(parse_image(image), (800, 0)))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cam_left.stop()
                cam_left.destroy()
                cam_right.stop()
                cam_right.destroy()
                vehicle.destroy()
                pygame.quit()
                return


if __name__ == '__main__':
    main()

import carla
import pygame
import numpy as np
import random

def main():
    # Set up your CARLA environment and pygame window here
    # Assuming client, world, blueprint_library, and vehicle are already set up
    client = carla.Client('localhost', 2000)
    client.set_timeout(3.0)
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()
    # Create camera for left mirror
    cam_bp = blueprint_library.find('sensor.camera.rgb')
    cam_bp.set_attribute('image_size_x', '800')
    cam_bp.set_attribute('image_size_y', '600')
    cam_bp.set_attribute('fov', '90')

    # Find a vehicle blueprint
    vehicle_bp = blueprint_library.find('vehicle.audi.a2')

    # Choose a spawn point. If no spawn point is specified, you might want to select one manually.
    spawn_points = world.get_map().get_spawn_points()
    random.shuffle(spawn_points)  # Shuffle to try spawns in random order

    # Try to spawn the vehicle at different points
    for spawn_point in spawn_points:
        try:
            vehicle = world.spawn_actor(vehicle_bp, spawn_point)
            print("Vehicle spawned successfully!")
            break
        except RuntimeError as e:
            print(f"Failed to spawn at this point due to: {str(e)}")
    else:
        print("Failed to spawn a vehicle, all spawn points checked.")  # Can select any valid point

    # Spawn the vehicle
    #vehicle = world.spawn_actor(vehicle_bp, spawn_points)


    # Make sure to add the vehicle to the simulation
    #actor_list.append(vehicle)
    pygame.init()
    display = pygame.display.set_mode((1600, 900))

    cam_transform_left = carla.Transform(carla.Location(x=0.5, y=-0.5, z=1.5), carla.Rotation(yaw=-45))
    cam_left = world.spawn_actor(cam_bp, cam_transform_left, attach_to=vehicle)

    # Create camera for right mirror
    cam_transform_right = carla.Transform(carla.Location(x=0.5, y=0.5, z=1.5), carla.Rotation(yaw=45))
    cam_right = world.spawn_actor(cam_bp, cam_transform_right, attach_to=vehicle)


    def parse_image(image):
        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        return surface

    while True:
        # Your game loop here
        # Capture images
        image_left = cam_left.listen(lambda image: parse_image(image))
        image_right = cam_right.listen(lambda image: parse_image(image))

        # Display images on pygame window
        display.blit(image_left, (0, 0))
        display.blit(image_right, (800, 0))  # Adjust positioning as needed

        pygame.display.flip()

    # Clean up
    cam_left.destroy()
    cam_right.destroy()

if __name__ == '__main__':
    main()

import time

import carla
import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
from carla import ColorConverter as cc


if sys.version_info >= (3, 0):

    from configparser import ConfigParser

else:

    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


import random
from sensors import CollisionSensor, LaneInvasionSensor, GnssSensor
import utils
import camera
import hud
import math
import threading


def destroy_actor( actor):
    """Function to destroy an actor."""
    if actor.is_alive:
        print(f"Destroying actor: {actor.id}")
        actor.destroy()
    else:
        print(f" {actor.id}: Actor already destroyed or does not exist.")
class World(object):
    def __init__(self, carla_world, hud, actor_filter):
        self.world = carla_world
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = utils.find_weather_presets()
        self._weather_index = 0
        self._actor_filter = actor_filter
        self.spawned_actors = []
        self.last_alerted_time = {}
        self.restart()
        self.world.on_tick(hud.on_world_tick)


    def restart(self):
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a random blueprint.
        blueprint_library = self.world.get_blueprint_library()
        blueprint = blueprint_library.find('vehicle.audi.a2')
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        # Spawn the player.
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0  # Adjust spawn height to prevent embedding in the ground
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()  # Destroy the current player vehicle before respawning
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        else:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = camera.CameraManager(self.player, self.hud)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = utils.get_actor_display_name(self.player)
        self.hud.notification(actor_type)


    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def tick(self, clock):
        self.hud.tick(self, clock)
        self.obstacle_ahead()

    def draw_speedometer(self, display, speed, center):
        max_speed = 220  # max speed in km/h
        radius = 45
        # Adjust angles for a full circle distribution
        for n in range(0, max_speed, 20):  # Adjust step and range as needed
            angle = math.radians((n - 160) / max_speed * 360)  # Adjust angle for 0 starting at 90 degrees
            # Calculate the positions for the start and end points of the ticks
            outer_point = (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))
            inner_point = (center[0] + (radius - 10) * math.cos(angle), center[1] + (radius - 10) * math.sin(angle))
            pygame.draw.line(display, (255, 255, 255), inner_point, outer_point, 2)
            # Adjust text positioning
            label_offset = 20  # Offset for text from the outer point
            text_surface = pygame.font.Font(None, 20).render(str(n), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(center[0] + (radius + label_offset) * math.cos(angle),
                                                      center[1] + (radius + label_offset) * math.sin(angle)))
            display.blit(text_surface, text_rect)

        # Draw the speedometer needle
        needle_angle = math.radians((speed - 160) / max_speed * 360)  # Adjust needle for 0 starting at 90 degrees
        end_point = (
        center[0] + (radius - 15) * math.cos(needle_angle), center[1] + (radius - 15) * math.sin(needle_angle))
        pygame.draw.line(display, (255, 0, 0), center, end_point, 2)
        pygame.draw.circle(display, (255, 255, 255), center, radius, 2)

    def draw_compass(self, display, heading, center):
        radius = 50
        font = pygame.font.Font(None, 24)
        labels = ['N', 'E', 'S', 'W']
        # Draw the directions
        for i, label in enumerate(labels):
            angle = math.radians(i * 90)
            label_pos = (center[0] + (radius + 20) * math.sin(angle), center[1] - (radius + 20) * math.cos(angle))
            text_surface = font.render(label, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=label_pos)
            display.blit(text_surface, text_rect)

        # Draw the compass needle
        angle = math.radians(heading)
        end_point = (center[0] + radius * math.sin(angle), center[1] - radius * math.cos(angle))
        pygame.draw.line(display, (0, 255, 0), center, end_point, 2)
        pygame.draw.circle(display, (255, 255, 255), center, radius, 2)

    def draw_gauge(self, display, value, max_value, center, label):
        if isinstance(value, str):  # Check if the value is a string (for gear display)
            angle = 0  # Default angle for gear, since it doesn't need a needle
        else:
            angle = value / max_value * 180  # Convert value to angle if numeric
        radius = 40
        needle_length = 35
        needle_angle = math.radians(angle - 180)
        end_point = (
        center[0] + needle_length * math.cos(needle_angle), center[1] + needle_length * math.sin(needle_angle))
        # Draw the gauge circle
        pygame.draw.circle(display, (255, 255, 255), center, radius, 2)
        if not isinstance(value, str):  # Draw the gauge needle if value is numeric
            pygame.draw.line(display, (255, 0, 0), center, end_point, 2)
        # Label the gauge
        font = pygame.font.Font(None, 20)
        text_surface = font.render(f"{label}", True, (255, 255, 255))
        display.blit(text_surface, (center[0] - radius / 2, center[1] - radius - 20))

    def draw_dashboard(self, display):
        # Dimensions and position of the dashboard
        dashboard_height = 150
        dashboard_top = display.get_height() - dashboard_height
        # Draw the dashboard background
        pygame.draw.rect(display, (30, 30, 30), pygame.Rect(0, dashboard_top, 1000, dashboard_height))

        # Set the center positions for the speedometer and compass within the dashboard
        speedometer_center = (650, display.get_height() - 75)
        compass_center = (850, display.get_height() - 75)

        # Assuming speed and heading are being updated somewhere in the code
        speed = 3.6 * math.sqrt(
            self.player.get_velocity().x ** 2 + self.player.get_velocity().y ** 2 + self.player.get_velocity().z ** 2)
        heading = self.player.get_transform().rotation.yaw

        positions = {
            'throttle': (200, display.get_height() - 75),
            #'brake': (200, display.get_height() - 75),
            'steer': (300, display.get_height() - 75),
            'handbrake': (400, display.get_height() - 75),
            #'gear': (500, display.get_height() - 75)
        }

        # Fetch control data from vehicle
        controls = self.player.get_control()
        #gear_display = str(controls.gear) if controls.gear >= 0 else 'R'

        # Draw the speedometer and compass using their respective functions
        self.draw_speedometer(display, speed, speedometer_center)
        self.draw_compass(display, heading, compass_center)
        self.draw_gauge(display, controls.throttle * 100, 100, positions['throttle'], 'Throttle')
        #self.draw_gauge(display, controls.brake * 100, 100, positions['brake'], 'Brake')
        self.draw_gauge(display, (controls.steer + 1) * 50, 100, positions['steer'], 'Steer')
        self.draw_gauge(display, controls.hand_brake * 100, 100, positions['handbrake'], 'Handbrake')
        #self.draw_gauge(display, gear_display, 1, positions['gear'], 'Gear')  # Pass gear as a string



    # def render(self, display):
    #     self.camera_manager.render(display)
    #     self.hud.render(display)
    #     # velocity = self.player.get_velocity()
    #     # speed = 3.6 * math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2)
    #     # # Draw the speedometer with the current speed
    #     # self.draw_speedometer(display, speed)
    #     #
    #     # heading = self.player.get_transform().rotation.yaw
    #     # # Draw the compass
    #     # self.draw_compass(display, heading)
    #
    #     self.draw_dashboard(display)

    # def render(self, display):
    #     self.camera_manager.render(display)
    #     self.hud.render(display)
    #
    #     # Check if the danger sign should still be visible
    #     if hasattr(self, 'danger_sign_start_time'):
    #         current_time = pygame.time.get_ticks()
    #         # Display danger sign for 3 seconds
    #         if current_time - self.danger_sign_start_time < 3000:  # 3000 milliseconds = 3 seconds
    #             display.blit(self.danger_sign_image, self.danger_sign_position)
    #         else:
    #             # Remove the danger sign after 3 seconds by removing the attribute
    #             del self.danger_sign_image
    #             del self.danger_sign_position
    #             del self.danger_sign_start_time
    #
    #     self.draw_dashboard(display)  # Call your other rendering functions

    def render(self, display,  traffic_light_icon=None):
        self.camera_manager.render(display)  # Render the camera view
        self.hud.render(display)  # Render the HUD (temporarily comment this if testing)
        if traffic_light_icon:
            display.blit(traffic_light_icon, (10, 10))
        # Check if the danger sign should still be visible
        if hasattr(self, 'danger_sign_start_time'):
            current_time = pygame.time.get_ticks()
            # Display danger sign for 3 seconds
            if current_time - self.danger_sign_start_time < 3000:  # 3000 milliseconds = 3 seconds
                display.blit(self.danger_sign_image, self.danger_sign_position)
            else:
                # Remove the danger sign after 3 seconds by removing the attribute
                del self.danger_sign_image
                del self.danger_sign_position
                del self.danger_sign_start_time

        # Render the dashboard last to ensure it appears on top of other elements
        self.draw_dashboard(display)  # Temporarily comment this if testing

    def destroy(self):
        sensors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor]
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.player is not None:
            self.player.destroy()

    # def obstacle_ahead(self):
    #     vehicle_transform = self.player.get_transform()
    #     vehicle_location = vehicle_transform.location
    #     vehicle_forward = vehicle_transform.get_forward_vector()
    #
    #     world = self.player.get_world()
    #     obstacles = self.spawned_actors  # Assuming all obstacles have a type prefixed by 'obstacle.'
    #
    #     closest_obstacle = None
    #     # min_distance = float('inf')
    #
    #     for obstacle in obstacles:
    #         obstacle_location = obstacle.get_transform().location
    #         vector_to_obstacle = obstacle_location - vehicle_location
    #         distance_to_obstacle = vector_to_obstacle.length()
    #
    #         # Normalize vectors to calculate the angle
    #         vehicle_forward_norm = vehicle_forward.make_unit_vector()
    #         vector_to_obstacle_norm = vector_to_obstacle.make_unit_vector()
    #         dot_product = vehicle_forward_norm.dot(vector_to_obstacle_norm)
    #         angle = math.acos(dot_product) * (180 / math.pi)  # Convert radians to degrees
    #
    #         # Check if the obstacle is within a reasonable angle and close enough
    #         if distance_to_obstacle < 50 and angle < 30:  # Example thresholds
    #             # if distance_to_obstacle < min_distance:
    #             #     min_distance = distance_to_obstacle
    #             closest_obstacle = obstacle
    #
    #         if closest_obstacle is not None:
    #             pygame.mixer.music.play()
    #         # Notify about the obstacle
    #             pygame.mixer.init()
    #             pygame.mixer.music.load("alert_tone.wav")
    #             self.hud.notification_obstacle("Obstacle Ahead", seconds=4.0)



    # def obstacle_ahead(self):
    #     pygame.mixer.init()
    #     pygame.mixer.music.load("alert_tone.wav")
    #     pygame.mixer.music.play()
    #
    #     if self.spawned_actors:
    #         for actor in self.spawned_actors:
    #             self.hud.notification_obstacle("Obstacle Ahead", seconds=4.0)

    # def obstacle_ahead(self):
    #     vehicle_transform = self.player.get_transform()
    #     vehicle_location = vehicle_transform.location
    #     vehicle_forward = vehicle_transform.get_forward_vector()
    #
    #
    #     for actor in self.spawned_actors:
    #         if actor.is_alive:
    #             obstacle_location = actor.get_transform().location
    #             vector_to_obstacle = obstacle_location - vehicle_location
    #             distance_to_obstacle = vector_to_obstacle.length()
    #
    #             # Normalize vectors to calculate the angle
    #             vehicle_forward_norm = vehicle_forward.make_unit_vector()
    #             vector_to_obstacle_norm = vector_to_obstacle.make_unit_vector()
    #             dot_product = vehicle_forward_norm.dot(vector_to_obstacle_norm)
    #             angle = math.acos(dot_product) * (180 / math.pi)  # Convert radians to degrees
    #
    #             # Check if the obstacle is within a reasonable angle and close enough
    #             if distance_to_obstacle < 50 and angle < 30:  # Example thresholds
    #                 pygame.mixer.init()
    #                 pygame.mixer.music.load("alert_tone.wav")
    #                 self.hud.notification_obstacle("Obstacle Ahead", seconds=4.0)
    #                 break
    #
    #           # Stop checking after the first found obstacle
    # def obstacle_ahead(self):
    #     vehicle_transform = self.player.get_transform()
    #     vehicle_location = vehicle_transform.location
    #     vehicle_forward = vehicle_transform.get_forward_vector()
    #
    #     world_map = self.world.get_map()
    #
    #     for actor in self.spawned_actors:
    #         if actor.is_alive:
    #             obstacle_location = actor.get_transform().location
    #             vector_to_obstacle = obstacle_location - vehicle_location
    #             distance_to_obstacle = vector_to_obstacle.length()
    #
    #             # Normalize vectors to calculate the angle
    #             vehicle_forward_norm = vehicle_forward.make_unit_vector()
    #             vector_to_obstacle_norm = vector_to_obstacle.make_unit_vector()
    #             dot_product = vehicle_forward_norm.dot(vector_to_obstacle_norm)
    #             angle = math.acos(dot_product) * (180 / math.pi)  # Convert radians to degrees
    #
    #             # Check if the obstacle is within a reasonable angle, close enough, and on the road
    #             waypoint = world_map.get_waypoint(obstacle_location, project_to_road=False)
    #
    #             if waypoint is not None and waypoint.lane_type == carla.LaneType.Driving:
    #                 if distance_to_obstacle < 50 and angle < 30:  # Additional checks
    #                     pygame.mixer.init()
    #                     pygame.mixer.music.load("alert_tone.wav")
    #                     pygame.mixer.music.play()
    #                     self.hud.notification_obstacle("Obstacle Ahead", seconds=4.0)
    #                     break  # Stop checking after the first found obstacle
    def obstacle_ahead(self):
        vehicle_transform = self.player.get_transform()
        vehicle_location = vehicle_transform.location
        vehicle_forward = vehicle_transform.get_forward_vector()

        current_time = time.time()
        alert_cooldown = 10  # seconds before a new alert can be triggered for the same obstacle
        world_map = self.world.get_map()
        for actor in self.spawned_actors:
            if actor.is_alive:
                obstacle_id = actor.id
                obstacle_location = actor.get_transform().location
                vector_to_obstacle = obstacle_location - vehicle_location
                distance_to_obstacle = vector_to_obstacle.length()

                vehicle_forward_norm = vehicle_forward.make_unit_vector()
                vector_to_obstacle_norm = vector_to_obstacle.make_unit_vector()
                dot_product = vehicle_forward_norm.dot(vector_to_obstacle_norm)
                dot_product = max(-1.0, min(1.0, dot_product))
                angle = math.acos(dot_product) * (180 / math.pi)
                waypoint = world_map.get_waypoint(obstacle_location, project_to_road=False)
                #
                if waypoint is not None and waypoint.lane_type == carla.LaneType.Driving:
                    if distance_to_obstacle < 30 and angle < 15:
                        last_alerted = self.last_alerted_time.get(obstacle_id, 0)
                        if (current_time - last_alerted) > alert_cooldown:
                        # Update the last alerted time
                            self.last_alerted_time[obstacle_id] = current_time
                            self.trigger_alert()

    # def trigger_alert(self):
    #     pygame.mixer.init()
    #     pygame.mixer.music.load("alert_tone.wav")
    #     pygame.mixer.music.play()
    #     self.hud.notification_obstacle("Obstacle Ahead", seconds=3.0)

    def trigger_alert(self):
        # Initialize the pygame mixer for playing alert sound
        pygame.mixer.init()
        pygame.mixer.music.load("alert_tone.wav")
        pygame.mixer.music.play()

        # Load the danger sign image
        danger_sign_image = pygame.image.load("danger_sign_image.jpg")

        # Set the size of the danger sign icon (adjust as necessary)
        danger_sign_image = pygame.transform.scale(danger_sign_image, (50, 50))  # Resizing the icon to 100x100 pixels

        self.danger_sign_image = danger_sign_image
        self.danger_sign_position = (50, 50)  # Position of the danger sign
        self.danger_sign_start_time = pygame.time.get_ticks()
        # Optionally, still show a notification in the HUD (if needed)
        #self.hud.notification_obstacle("Obstacle Ahead", seconds=3.0)

    def spawn_obstacles(self):
        for _ in range(random.randint(1, 3)):  # Random number of obstacles
            spawn_distance = random.randint(100, 200)
            lateral_offset = random.randint(-10, 10)
            forward_vector = self.player.get_transform().get_forward_vector()
            right_vector = carla.Vector3D(x=-forward_vector.y, y=forward_vector.x)
            spawn_point = self.player.get_transform().location + carla.Location(
                x=spawn_distance * forward_vector.x + lateral_offset * right_vector.x,
                y=spawn_distance * forward_vector.y + lateral_offset * right_vector.y)
            spawn_point.z += 0.0

            blueprint = self.world.get_blueprint_library().find(random.choice([
                'static.prop.warningaccident', 'static.prop.trafficwarning',
                'static.prop.warningconstruction', 'static.prop.container',
                'static.prop.trafficcone01', 'static.prop.trashcan03',
                'static.prop.travelcase', 'static.prop.shoppingtrolley',
                'static.prop.shoppingcart', 'static.prop.bin'
            ]))

            spawned_actor = self.world.try_spawn_actor(blueprint, carla.Transform(spawn_point))
            # if spawned_actor is not None:
            #     self.spawned_obstacles.append(spawned_actor)  # Add to the tracking list
            if spawned_actor is not None:
                self.spawned_actors.append(spawned_actor)
                print(f"{spawned_actor.id} is spawned at {time.time()}")
                # self.obstacle_ahead()
                # print(f"Spawned actor at: {spawn_point}")
                # Scheduling the actor to be destroyed after 30 seconds
                #threading.Timer(30, lambda: self.destroy_actor(spawned_actor)).start()
                threading.Timer(30, destroy_actor, args=[spawned_actor]).start()




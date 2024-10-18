

from __future__ import print_function


# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================


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


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import threading
import carla

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
####
from world import World
from hud import HUD
from control import DualControl
import pygame
import logging
import argparse
import time
import utils
import random

# def game_loop(args):
#     pygame.init()
#     pygame.font.init()
#     world = None
#
#     try:
#         client = carla.Client(args.host, args.port)
#         client.set_timeout(3.0)
#
#         display = pygame.display.set_mode(
#             (args.width, args.height),
#             pygame.HWSURFACE | pygame.DOUBLEBUF)
#
#         hud = HUD(args.width, args.height)
#         world = World(client.get_world(), hud, args.filter)
#         controller = DualControl(world, args.autopilot)
#
#         clock = pygame.time.Clock()
#         last_spawn_time = time.time()
#         while True:
#             clock.tick_busy_loop(60)
#             if controller.parse_events(world, clock):
#                 return
#
#             # current_time = time.time()
#             # if current_time - last_spawn_time >= 10:
#             #     world.spawn_obstacles()
#             #     last_spawn_time = current_time
#             if random.random() < 0.01:  # Adjust this value to increase or decrease frequency
#                 world.spawn_obstacles()
#
#
#                 # Traffic light detection
#             # traffic_light = utils.find_traffic_light(world.player)
#             # light_state = utils.get_traffic_light_state(traffic_light)
#             # if light_state is not 0:
#             #     hud.notification_traffic_light(f"Traffic Light: {light_state}")
#
#
#             ####### Neew ###########
#             # Traffic light detection
#
#             traffic_light = utils.find_traffic_light(world.player)
#             light_state = utils.get_traffic_light_state(traffic_light)
#
#             # Load traffic light images (red, yellow, green)
#             red_icon = pygame.image.load("Red.png")
#             yellow_icon = pygame.image.load("Yellow.png")
#             green_icon = pygame.image.load("Green.png")
#
#             # Resize the images if needed (adjust dimensions as necessary)
#             red_icon = pygame.transform.scale(red_icon, (50, 50))
#             yellow_icon = pygame.transform.scale(yellow_icon, (50, 50))
#             green_icon = pygame.transform.scale(green_icon, (50, 50))
#
#             # Display the appropriate icon based on the traffic light state
#             if light_state == "Red":
#                 display.blit(red_icon, (10, 10))  # Change (10, 10) to the desired position
#             elif light_state == "Yellow":
#                 display.blit(yellow_icon, (10, 10))  # Change (10, 10) to the desired position
#             elif light_state == "Green":
#                 display.blit(green_icon, (10, 10))  # Change (10, 10) to the desired position
# #############################################
#             world.tick(clock)
#             world.render(display)
#             pygame.display.flip()
#
#     finally:
#
#         if world is not None:
#             #world.clear_actor_cache()
#             world.destroy()
#
#         pygame.quit()
def game_loop(args):
    pygame.init()
    pygame.font.init()
    world = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(3.0)

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args.width, args.height)
        world = World(client.get_world(), hud, args.filter)
        controller = DualControl(world, args.autopilot)

        clock = pygame.time.Clock()
        last_spawn_time = time.time()
        # Load traffic light images
        try:
            red_icon = pygame.image.load("Red.png")
            yellow_icon = pygame.image.load("Yellow.png")
            green_icon = pygame.image.load("Green.png")
        except pygame.error as e:
            print(f"Failed to load traffic light images: {e}")
            return  # Exit if images can't be loaded

        # Resize images (optional)
        red_icon = pygame.transform.scale(red_icon, (126, 41))
        yellow_icon = pygame.transform.scale(yellow_icon, (126, 41))
        green_icon = pygame.transform.scale(green_icon, (126, 41))

        while True:
            clock.tick_busy_loop(60)

            if controller.parse_events(world, clock):
                return
            # current_time = time.time()
            # if current_time - last_spawn_time >= 10:
            #     world.spawn_obstacles()
            #     last_spawn_time = current_time
            # # if random.random() < 0.01:  # Adjust this value to increase or decrease frequency
            # #     world.spawn_obstacles()
            # Traffic light detection logic
            traffic_light = utils.find_traffic_light(world.player)
            light_state = utils.get_traffic_light_state(traffic_light)

            # Clear the display before rendering
            display.fill((0, 0, 0))  # Black background

            # Determine which traffic light icon to display
            if light_state == "Red":
                #print("Red traffic light")
                traffic_light_icon = red_icon
            elif light_state == "Yellow":
                #print("Yellow traffic light")
                traffic_light_icon = yellow_icon
            elif light_state == "Green":
                #print("Green traffic light")
                traffic_light_icon = green_icon
            else:
                traffic_light_icon = None
#########################################
            # transform = world.player.get_transform()
            #
            # # Extract location from the transform
            # location = transform.location
            #
            # # Print the x, y, z coordinates of the car
            # print(f"Car's Location: x={location.x}, y={location.y}, z={location.z}")

            ################# Lane
            # transform = world.player.get_transform()
            #
            # # Get the CARLA map from the world
            # carla_map = world.world.get_map()
            #
            # # Get the waypoint at the player's current location
            # waypoint = carla_map.get_waypoint(transform.location)
            #
            # # Ensure the waypoint is not None (valid waypoint)
            # if waypoint is not None:
            #     # Check if the lane is a driving lane (to exclude parking or sidewalks)
            #     if waypoint.lane_type == carla.LaneType.Driving:
            #         lane_id = waypoint.lane_id
            #
            #         # Ignore lanes on the opposite side (lane_id < 0)
            #         if lane_id < 0:
            #             if lane_id == 1:
            #                 print("The car is in the right lane (slow lane).")
            #             elif lane_id == 2:
            #                 print("The car is in the left lane (fast lane).")
            #             else:
            #                 print(f"Driving in lane ID: {lane_id}")
            #         else:
            #             print("The car is on the opposite side of the road. Ignoring this lane.")
            #     else:
            #         print("The car is not in a driving lane (e.g., on a sidewalk or parking).")
            # else:
            #     print("Could not retrieve the waypoint. The car might be off-road.")

            ###########################
            # Render the world, passing the traffic light icon
            # Show lane change information
            #utils.show_lane_change_info(world)
            world.tick(clock)

            ############## 10/ 17/24
            #world.render(display, traffic_light_icon=traffic_light_icon)
            lane_change_icon, lane_change_text = utils.show_lane_change_info( world)
            world.render(display, lane_change_icon=lane_change_icon, lane_change_text=lane_change_text)
            ################

            # Update the display after rendering everything
            pygame.display.flip()

    finally:
        if world is not None:
            world.destroy()

        pygame.quit()


# def game_loop(args):
#     pygame.init()
#     pygame.font.init()
#     world = None
#
#     try:
#         client = carla.Client(args.host, args.port)
#         client.set_timeout(3.0)
#
#         display = pygame.display.set_mode(
#             (args.width, args.height),
#             pygame.HWSURFACE | pygame.DOUBLEBUF)
#
#         hud = HUD(args.width, args.height)
#         world = World(client.get_world(), hud, args.filter)
#         controller = DualControl(world, args.autopilot)
#
#         clock = pygame.time.Clock()
#         last_spawn_time = time.time()
#
#         # Load traffic light images (red, yellow, green)
#         red_icon = pygame.image.load("Red.png")
#         yellow_icon = pygame.image.load("Yellow.png")
#         green_icon = pygame.image.load("Green.png")
#
#         # Resize the images if needed (adjust dimensions as necessary)
#         red_icon = pygame.transform.scale(red_icon, (50, 50))
#         yellow_icon = pygame.transform.scale(yellow_icon, (50, 50))
#         green_icon = pygame.transform.scale(green_icon, (50, 50))
#
#         while True:
#             clock.tick_busy_loop(60)
#             if controller.parse_events(world, clock):
#                 return
#
#             if random.random() < 0.01:  # Adjust this value to increase or decrease frequency
#                 world.spawn_obstacles()
#
#             # Traffic light detection
#             traffic_light = utils.find_traffic_light(world.player)
#             light_state = utils.get_traffic_light_state(traffic_light)
#
#             # Clear the screen before rendering (optional but recommended)
#             display.fill((0, 0, 0))  # Black background, you can change this
#
#             # Display the appropriate icon based on the traffic light state
#
#             if light_state == "Red":
#                 print("Red is ok")
#                 try:
#                     red_icon = pygame.image.load("Red.png")
#                     # Change (10, 10) to the desired position
#                     print("Images loaded successfully")
#                     display.blit(red_icon, (10, 10))
#                 except pygame.error as e:
#                     print(f"Failed to load images: {e}")
#             elif light_state == "Yellow":
#                 print("Yellow is ok")
#                 display.blit(yellow_icon, (10, 10))  # Change (10, 10) to the desired position
#             elif light_state == "Green":
#                 print("Green is ok")
#                 display.blit(green_icon, (10, 10))  # Change (10, 10) to the desired position
#
#             world.tick(clock)
#             world.render(display)
#
#             # Update the display after drawing the icons
#             pygame.display.flip()
#
#     finally:
#         if world is not None:
#             world.destroy()
#
#         pygame.quit()



# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:

        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':

    main()

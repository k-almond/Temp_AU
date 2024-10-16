import carla
import re


def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


import math
def find_traffic_light(vehicle, distance_threshold=50, angle_threshold=30):
    #Finding the traffic light directly facing the vehicle within a certain distance and angle.
    vehicle_transform = vehicle.get_transform()
    vehicle_location = vehicle_transform.location
    vehicle_forward = vehicle_transform.get_forward_vector()

    world = vehicle.get_world()
    lights = world.get_actors().filter('traffic.traffic_light')

    best_light = None
    min_angle = float('inf')

    for light in lights:
        #distacen between car and traffic light (points)
        light_location = light.get_transform().location
        vector_to_light = light_location - vehicle_location
        distance_to_light = vector_to_light.length()

        # Normalizing vectors to calculate the angle
        # converting vectors to unit vectors (magnitude of 1)
        vehicle_forward_norm = vehicle_forward.make_unit_vector()
        #print(vehicle_forward_norm)
        vector_to_light_norm = vector_to_light.make_unit_vector()
        dot_product = vehicle_forward_norm.dot(vector_to_light_norm)
        try:
            angle = math.acos(dot_product) * (180 / math.pi)  # Convert radians to degrees
        except ValueError:
            angle = 180  # Set angle to max if acos fails, though clamping should prevent this

        # Checking if the traffic light is within the angle and distance threshold
        if distance_to_light < distance_threshold and angle < angle_threshold:
            if angle < min_angle:
                min_angle = angle
                best_light = light

    return best_light

# def find_traffic_light(vehicle, distance_threshold=50):
#     """Find the traffic light in front of the vehicle within a certain distance."""
#     # Get the location and forward vector of the vehicle
#     vehicle_location = vehicle.get_transform().location
#     print(f"vehicle location: {vehicle_location}")
#     vehicle_forward = vehicle.get_transform().get_forward_vector()
#     print(f"vehicle forward: {vehicle_forward}")
#     # Get all the traffic lights from the world
#     world = vehicle.get_world()
#     lights = world.get_actors().filter('traffic.traffic_light')
#
#     # Check each traffic light to see if it's in front of the vehicle and within the distance threshold
#     for light in lights:
#         light_location = light.get_transform().location
#         print(f"light location: {light_location}")
#         vector_to_light = light_location - vehicle_location
#         distance_to_light = vector_to_light.length()
#         print(distance_to_light)
#         #print(light)
#         print(light.get_state())
#
#
#         # Calculate the dot product to see if the light is in front of the vehicle
#         if vector_to_light.dot(vehicle_forward) > 0 and distance_to_light < distance_threshold:
#             return light
#     print("__________________________")
#     return None


def get_traffic_light_state(light):
    """Return the state of the traffic light."""
    if light is None:
        return 0

    state = light.get_state()
    if state == carla.TrafficLightState.Red:
        #print(f"{light}- Red")
        return "Red"
    elif state == carla.TrafficLightState.Yellow:
        #print(f"{light}- Yellow")
        return "Yellow"
    elif state == carla.TrafficLightState.Green:
        #print(f"{light}- Green")
        return "Green"
    return "Off"


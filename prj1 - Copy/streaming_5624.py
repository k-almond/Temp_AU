import cv2
import mss
import numpy as np
import win32gui

def find_pygame_window(window_title):
    window_handle = win32gui.FindWindow(None, window_title)
    if window_handle != 0:
        window_rect = win32gui.GetWindowRect(window_handle)
        x, y, _, _ = window_rect
        return x, y
    else:
        return None


def stream_multiple_screen_areas(pygame_position, monitor_areas):
    with mss.mss() as sct:
        windows = {}
        # Calculate absolute positions based on pygame window location
        pygame_x, pygame_y = pygame_position

        for i, area in enumerate(monitor_areas):
            top = area['top'] + pygame_y
            left = area['left'] + pygame_x
            width = area['width']
            height = area['height']

            monitor = {
                "top": top,
                "left": left,
                "width": width,
                "height": height
            }
            window_name = f"Screen Stream {i}"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            windows[window_name] = monitor

        try:
            while True:
                for window_name, monitor in windows.items():
                    img = sct.grab(monitor)
                    if img:
                        frame = np.array(img)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        cv2.imshow(window_name, frame)
                    if cv2.waitKey(25) & 0xFF == ord('q'):
                        break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cv2.destroyAllWindows()

monitor_areas = [
    {"top": 23, "left": 8, "width": 1000, "height": 768},  # Dashboard 0
    {"top": 20, "left": 1010, "width": 350, "height": 200},  # Left mirror 1
    {"top": 220, "left": 1010, "width": 350, "height": 200},  # Right mirror 2
    {"top": 460, "left": 1010, "width": 200, "height": 100}  # Rear camera 3
]
# Assuming your Pygame window is found and its top-left corner is at (pygame_x, pygame_y)
pygame_position = find_pygame_window("pygame window")  # Ensure you pass the correct title
if pygame_position:
    stream_multiple_screen_areas(pygame_position, monitor_areas)
else:
    print("Pygame window not found")


# Example usage to stream different areas of screen with different windows


#stream_multiple_screen_areas(monitor_areas)

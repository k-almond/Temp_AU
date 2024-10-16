import cv2
import mss
import numpy as np
import win32gui
import time

def find_pygame_window(window_title):
    window_handle = win32gui.FindWindow(None, window_title)
    if window_handle != 0:
        window_rect = win32gui.GetWindowRect(window_handle)
        x, y, _, _ = window_rect
        return x, y
    else:
        return None

def stream_multiple_screen_areas(pygame_position, monitor_areas, fps=20, resize=None):
    with mss.mss() as sct:
        windows = {}
        pygame_x, pygame_y = pygame_position
        frame_interval = 1.0 / fps  # Frame interval in seconds

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
            last_time = time.time()
            while True:
                current_time = time.time()
                if current_time - last_time >= frame_interval:
                    for window_name, monitor in windows.items():
                        img = sct.grab(monitor)
                        if img:
                            frame = np.array(img)
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                            if resize:
                                frame = cv2.resize(frame, resize)
                            cv2.imshow(window_name, frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                    last_time = current_time
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cv2.destroyAllWindows()
monitor_areas = [
    {"top": 100, "left": 8, "width": 1000, "height": 700},  # Dashboard 0
    {"top": 20, "left": 8, "width": 1000, "height": 600},  # Dashboard noti 1
    {"top": 20, "left": 1017, "width": 350, "height": 200},  # Left mirror 2
    {"top": 240, "left": 1017, "width": 350, "height": 200},  # Right mirror 3
    {"top": 470, "left": 1017, "width": 200, "height": 90}  # Rear camera 3
]
# Example usage with FPS limit and optional resizing
pygame_position = find_pygame_window("pygame window")
if pygame_position:
    stream_multiple_screen_areas(pygame_position, monitor_areas, fps=30)
else:
    print("Pygame window not found")

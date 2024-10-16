import win32gui

def get_window_position(window_title):
    window_handle = win32gui.FindWindow(None, window_title)
    if window_handle != 0:
        window_rect = win32gui.GetWindowRect(window_handle)
        x, y, _, _ = window_rect
        return x, y
    else:
        return None

# Example usage:
window_title = "pygame window"
position = get_window_position(window_title)
if position:
    print("Window position:", position)
else:
    print("Window not found.")

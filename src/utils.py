import tkinter as tk


def set_window_size_and_position(window, width, height):
    """
    Set the window size and position, ensuring it doesn't exceed the screen size.
    
    Args:
        window: The tkinter window or dialog
        width: The desired width of the window
        height: The desired height of the window
    """
    # Get screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate maximum allowed width and height
    max_width = min(width, screen_width)
    max_height = min(height, screen_height)

    # Set window size
    window.geometry(f"{max_width}x{max_height}")

    # Center the window on the screen
    x = (screen_width - max_width) // 2
    y = (screen_height - max_height) // 2
    window.geometry(f"+{x}+{y}")

"""
Roblox Player Counter - System Tray Application
Displays current player count on a tray icon with automatic updates.
"""

import tkinter as tk
import requests
import sys
import threading
from shutil import rmtree
from tempfile import mkdtemp
from PIL import Image, ImageDraw, ImageFont
import pystray


# Configuration
API_URL = "https://games.roblox.com/v1/games?universeIds=917412830"
UPDATE_INTERVAL = 10  # seconds
ICON_SIZE = 128
FONT_PATH = "C:\\Windows\\Fonts\\Arial.ttf"
FONT_SIZE = 70

# Global state
current_count = "..."
tray_icon = None
stop_event = threading.Event()
temp_icon_dir = mkdtemp()
root = None


def create_tray_icon(text):
    """Create a red circular tray icon with centered player count text."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Red circle background
    draw.ellipse((4, 4, ICON_SIZE - 4, ICON_SIZE - 4), fill=(226, 35, 26, 255))

    # Load font with fallback
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    draw.text(
        ((ICON_SIZE - text_width) / 2, (ICON_SIZE - text_height) / 2 - 4),
        text,
        fill="white",
        font=font
    )

    return img


def on_quit(icon, item):
    """Handle quit action from tray menu."""
    stop_event.set()
    icon.stop()
    root.after(0, root.quit)


def update_menu(count_text):
    """Update tray menu and icon."""
    global current_count, tray_icon
    current_count = count_text
    
    if not tray_icon:
        return
    
    try:
        # Update icon and tooltip
        tray_icon.icon = create_tray_icon(count_text)
        tray_icon.title = f"Area 27 Players: {count_text}"
        
        # Update menu
        tray_icon.menu = pystray.Menu(
            pystray.MenuItem(f"Area 27 Players: {count_text}", lambda: None),
            pystray.MenuItem("Exit", on_quit)
        )
    except Exception as e:
        print(f"Error updating tray: {e}")


def fetch_player_count():
    """Fetch current player count from Roblox API."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()["data"]
        count = int(data[0]["playing"])
        return str(min(count, 99))
    except Exception as e:
        print(f"API error: {e}")
        return "?"


def api_update_loop():
    """Background thread that periodically updates the tray icon."""
    while not stop_event.is_set():
        count = fetch_player_count()
        update_menu(count)
        print(f"Players online: {count}")
        stop_event.wait(UPDATE_INTERVAL)


def show_in_tray():
    """Start the tray icon with menu."""
    global tray_icon
    
    menu = pystray.Menu(
        pystray.MenuItem(f"Area 27 Players: {current_count}", lambda: None),
        pystray.MenuItem("Exit", on_quit)
    )
    
    icon_image = create_tray_icon(current_count)
    tray_icon = pystray.Icon("Area 27 Counter", icon_image, menu=menu)
    tray_icon.run()


def main():
    """Initialize and run the application."""
    global root
    
    print("Starting Area 27 Player Counter...")

    # Create hidden Tkinter window for event loop
    root = tk.Tk()
    root.title("Area 27 Player Counter")
    root.withdraw()

    # Start tray icon in background thread
    threading.Thread(target=show_in_tray, daemon=True).start()

    # Start API update thread
    threading.Thread(target=api_update_loop, daemon=True).start()

    # Run main event loop
    try:
        root.mainloop()
    finally:
        # Cleanup
        stop_event.set()
        if tray_icon:
            try:
                tray_icon.stop()
            except Exception:
                pass
        
        # Clean up temporary directory
        try:
            rmtree(temp_icon_dir)
        except Exception:
            pass
        
        sys.exit(0)


if __name__ == "__main__":
    main()

"""Application constants and bundled-file lookup, shared by every platform."""
import os
import sys

APP_NAME = "Screen Preview"
APP_VERSION = "dev"   # stamped by CI on release tags
REPO_URL = "https://github.com/Ookean/screen-previewer"
PRIVACY_URL = f"{REPO_URL}/blob/main/PRIVACY.md"


def resource_path(name):
    """Find a bundled data file (PyInstaller) or one in the repo root (running from source)."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


# Wayland sessions forbid reading the screen and moving other apps' windows without a permission dialog.
ON_WAYLAND = sys.platform != "win32" and (
    bool(os.environ.get("WAYLAND_DISPLAY")) or os.environ.get("XDG_SESSION_TYPE") == "wayland")

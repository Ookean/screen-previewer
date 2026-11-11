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


def desktop_info():
    """A short description of the user's system, for support requests: desktop, session type, distribution."""
    session = os.environ.get("XDG_SESSION_TYPE") or ("wayland" if ON_WAYLAND else "unknown session")
    parts = [os.environ.get("XDG_CURRENT_DESKTOP") or "unknown desktop", session]
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    parts.append(line.split("=", 1)[1].strip().strip('"'))
    except OSError:
        pass
    return ", ".join(parts)

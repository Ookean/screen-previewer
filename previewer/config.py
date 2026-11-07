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
"""User settings, stored as a small JSON file in the user's config folder."""
import json
import os
import sys

APP_FOLDER = "ScreenPreview"


def default_settings_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_FOLDER, "settings.json")


class Settings:
    """Saved preferences. A missing, unreadable or broken file simply gives the defaults."""

    DEFAULTS = {"language": "system"}   # "system" = follow the operating system

    def __init__(self, path=None):
        self.path = path or default_settings_path()
        self.values = dict(self.DEFAULTS)
        self._load()

    @property
    def language(self):
        return self.values["language"]

    def set_language(self, code):
        self.values["language"] = code
        self.save()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.values, f, indent=2)
        except OSError as e:
            print(f"Could not save settings: {e}")

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        for key, default in self.DEFAULTS.items():
            if isinstance(data.get(key), type(default)):
                self.values[key] = data[key]

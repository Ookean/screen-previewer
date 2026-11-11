"""Window control on Wayland.

Wayland lets only the desktop (the compositor) move windows, so every desktop needs its own backend:
KDE Plasma, Sway and Hyprland are supported. On any other desktop (GNOME, for example) the controls are
disabled and the user is asked to report their desktop so support can be added.

Same public names as the Windows and X11 implementations, plus:
    ZOOM_AVAILABLE, ZOOM_UNAVAILABLE_REASON   zoom needs the desktop backend *and* the key portal
    list_monitors()                           the desktop's real screens (the preview picks its own screen)
"""
import os

from ..layouts import compute_placement
from . import hyprland, kde, sway
from .common import Window  # noqa: F401  (re-exported)
from .keys import ZoomKeys


def _detect():
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "kde" in desktop:
        return kde
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return hyprland
    if os.environ.get("SWAYSOCK"):
        return sway
    return None


_backend = _detect()
AVAILABLE = _backend is not None and _backend.usable()
UNAVAILABLE_REASON = None if AVAILABLE else ("window.unavailable" if _backend else "window.unavailable_wayland")

try:
    import jeepney  # noqa: F401
    _HAVE_PORTAL = True
except ImportError:
    _HAVE_PORTAL = False
ZOOM_AVAILABLE = AVAILABLE and _HAVE_PORTAL
ZOOM_UNAVAILABLE_REASON = None if ZOOM_AVAILABLE else UNAVAILABLE_REASON or "window.unavailable"

_keys = ZoomKeys()


def enable_dpi_awareness():
    """Nothing to do on Linux; present so callers need no platform check."""


def list_windows():
    return _backend.windows()


def list_monitors():
    return _backend.monitors() if AVAILABLE else []


def arrange(window, monitor, layout="center"):
    _backend.place(window, compute_placement(monitor, layout, window.width, window.height))


def zoom(window, action):
    _backend.focus(window)
    _keys.send(action)

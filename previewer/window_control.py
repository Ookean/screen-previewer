"""Window listing, layouts and zoom: picks the implementation for the current platform.

Public names (same on every platform):
    AVAILABLE, UNAVAILABLE_REASON   whether window control works here; if not, a locale key saying why
    LAYOUTS, compute_placement      layout ids and the geometry maths (layouts.py)
    enable_dpi_awareness(), list_windows(), arrange(window, monitor, layout), zoom(window, action)
"""
import sys

from .layouts import LAYOUTS, Placement, compute_placement  # noqa: F401  (re-exported)

if sys.platform == "win32":
    from . import _win32 as _impl
else:
    from . import _x11 as _impl

AVAILABLE = _impl.AVAILABLE
UNAVAILABLE_REASON = _impl.UNAVAILABLE_REASON
enable_dpi_awareness = _impl.enable_dpi_awareness
list_windows = _impl.list_windows
arrange = _impl.arrange
zoom = _impl.zoom

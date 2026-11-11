"""Window listing, layouts and zoom: picks the implementation for the current platform.

Public names (same on every platform):
    AVAILABLE, UNAVAILABLE_REASON   whether listing/moving windows works here; if not, a locale key saying why
    ZOOM_AVAILABLE                  whether the zoom buttons work (separate: Wayland needs extra for it)
    NEEDS_SUPPORT_REPORT            True on a Wayland desktop that is not fully supported: ask the user to report it
    list_monitors                   the desktop's own screen list, or None to use the capture's list
    LAYOUTS, compute_placement      layout ids and the geometry maths (layouts.py)
    enable_dpi_awareness(), list_windows(), arrange(window, monitor, layout), zoom(window, action)
"""
import sys

from .config import ON_WAYLAND
from .layouts import LAYOUTS, Placement, compute_placement  # noqa: F401  (re-exported)

if sys.platform == "win32":
    from . import _win32 as _impl
elif ON_WAYLAND:
    from . import wayland as _impl
else:
    from . import _x11 as _impl

AVAILABLE = _impl.AVAILABLE
UNAVAILABLE_REASON = _impl.UNAVAILABLE_REASON
ZOOM_AVAILABLE = getattr(_impl, "ZOOM_AVAILABLE", _impl.AVAILABLE)
list_monitors = getattr(_impl, "list_monitors", None)
NEEDS_SUPPORT_REPORT = ON_WAYLAND and not (AVAILABLE and ZOOM_AVAILABLE)
enable_dpi_awareness = _impl.enable_dpi_awareness
list_windows = _impl.list_windows
arrange = _impl.arrange
zoom = _impl.zoom

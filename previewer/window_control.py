import ctypes
import time
from dataclasses import dataclass
from typing import Optional

try:
    import pygetwindow as gw
    import win32api
    import win32con
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

UNAVAILABLE_MESSAGE = "pygetwindow/pywin32 not installed (pip install -r requirements.txt)"
LAYOUTS = ["Center", "Maximize", "Left half", "Right half", "Top half", "Bottom half"]
ZOOM_KEYS = {"in": 0xBB, "out": 0xBD, "reset": 0x30}  # VK_OEM_PLUS, VK_OEM_MINUS, '0'


@dataclass
class Placement:
    x: int
    y: int
    width: Optional[int] = None    # None = keep the window's current size
    height: Optional[int] = None
    maximize: bool = False


def compute_placement(monitor, layout, win_width, win_height):
    """Where a window of the given size should go on `monitor` for `layout`."""
    left, top = monitor["left"], monitor["top"]
    width, height = monitor["width"], monitor["height"]

    if layout == "Left half":
        return Placement(left, top, width // 2, height)
    if layout == "Right half":
        return Placement(left + width // 2, top, width - width // 2, height)
    if layout == "Top half":
        return Placement(left, top, width, height // 2)
    if layout == "Bottom half":
        return Placement(left, top + height // 2, width, height - height // 2)

    # "Center" and "Maximize": move first, so a maximize happens on the target monitor.
    x = left + max(0, (width - win_width) // 2)
    y = top + max(0, (height - win_height) // 2)
    return Placement(x, y, maximize=(layout == "Maximize"))


def enable_dpi_awareness():
    """Keep window coordinates in real pixels. Call before any window is created."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def list_windows():
    return [w for w in gw.getAllWindows()
            if w.title.strip() and w.visible and w.width > 0 and w.height > 0]


def arrange(window, monitor, layout="Center"):
    """Move a window onto a monitor and arrange it according to `layout`."""
    if window.isMinimized or window.isMaximized:
        window.restore()

    p = compute_placement(monitor, layout, window.width, window.height)
    window.moveTo(p.x, p.y)
    if p.width is not None:
        window.resizeTo(p.width, p.height)
        window.moveTo(p.x, p.y)  # second move corrects drift between monitors with different DPI
    if p.maximize:
        window.maximize()


def zoom(window, action):
    """Send Ctrl+Plus / Ctrl+Minus / Ctrl+0 to the window (browsers, viewers, Office...)."""
    if window.isMinimized:
        window.restore()
    try:
        window.activate()
    except Exception:
        pass  # pygetwindow can raise a spurious error even when activation worked
    time.sleep(0.15)

    key = ZOOM_KEYS[action]
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(key, 0, 0, 0)
    win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
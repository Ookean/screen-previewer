"""Window control on Windows (pygetwindow + pywin32)."""
import ctypes
import time

from .layouts import compute_placement

try:
    import pygetwindow as gw
    import win32api
    import win32con
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

UNAVAILABLE_REASON = None if AVAILABLE else "window.unavailable"
ZOOM_KEYS = {"in": 0xBB, "out": 0xBD, "reset": 0x30}  # VK_OEM_PLUS, VK_OEM_MINUS, '0'


def enable_dpi_awareness():
    """Keep window coordinates in real pixels. Call before any window is created."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def list_windows():
    return [w for w in gw.getAllWindows()
            if w.title.strip() and w.visible and w.width > 0 and w.height > 0]


def arrange(window, monitor, layout="center"):
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

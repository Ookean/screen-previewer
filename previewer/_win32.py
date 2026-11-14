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


def focus_own_window(root):
    """Bring this app's window back to the front after zoom or maximize activated another window."""
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()   # Tk's id is a child of the real top-level window
    foreground = user32.GetForegroundWindow()
    if foreground == hwnd:
        return
    # Windows only lets the program that owns the foreground take it over. Sharing its input queue
    # for a moment gets around that without sending any fake key presses to the other window.
    other = user32.GetWindowThreadProcessId(foreground, None)
    mine = kernel32.GetCurrentThreadId()
    attached = bool(other and other != mine and user32.AttachThreadInput(mine, other, True))
    try:
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(mine, other, False)


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

"""Window control on Linux under an X11 session (python-xlib, EWMH window manager hints).

Needs an X11 session. Wayland compositors do not let one app move another app's windows,
so there `AVAILABLE` is False and the controls are disabled.
"""
import time
from dataclasses import dataclass

from .config import ON_WAYLAND
from .layouts import compute_placement

try:
    from Xlib import X, XK, display, protocol
    from Xlib.ext import xtest
    _HAVE_XLIB = True
except ImportError:
    _HAVE_XLIB = False

AVAILABLE = _HAVE_XLIB and not ON_WAYLAND
UNAVAILABLE_REASON = None if AVAILABLE else ("window.unavailable_wayland" if ON_WAYLAND else "window.unavailable")

# _NET_WM_STATE actions
_REMOVE, _ADD = 0, 1
# _NET_MOVERESIZE_WINDOW flags: bits 8-11 say which of x, y, width, height are set; bits 12-15 = source (2: pager/tool)
_X, _Y, _W, _H = 1 << 8, 1 << 9, 1 << 10, 1 << 11
_FROM_PAGER = 2 << 12
_ZOOM_KEYSYMS = {"in": "equal", "out": "minus", "reset": "0"}   # Ctrl+= zooms in on a US *and* most other layouts

_display = None


@dataclass
class Window:
    id: int
    title: str
    width: int
    height: int


def enable_dpi_awareness():
    """Nothing to do on Linux; present so callers need no platform check."""


def _dpy():
    global _display
    if _display is None:
        _display = display.Display()
    return _display


def _atom(name):
    return _dpy().intern_atom(name)


def _prop(win, name, prop_type=X.AnyPropertyType if _HAVE_XLIB else 0):
    reply = win.get_full_property(_atom(name), prop_type)
    return None if reply is None else reply.value


def _title(win):
    value = _prop(win, "_NET_WM_NAME")
    if value is None:
        value = _prop(win, "WM_NAME")
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    return (value or "").strip()


def _states(win):
    value = _prop(win, "_NET_WM_STATE")
    return set(value) if value is not None else set()


def _send(win, message, data, mask=None):
    """Send a client message to the root window, the way EWMH asks pagers and taskbars to."""
    root = _dpy().screen().root
    event = protocol.event.ClientMessage(window=win, client_type=_atom(message), data=(32, data))
    root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    _dpy().flush()


def _set_state(win, action, *names):
    atoms = [_atom(n) for n in names] + [0] * (2 - len(names))
    _send(win, "_NET_WM_STATE", [action, atoms[0], atoms[1], 1, 0])


def _activate(win):
    _send(win, "_NET_ACTIVE_WINDOW", [2, X.CurrentTime, 0, 0, 0])


def _resolve(window):
    return _dpy().create_resource_object("window", window.id)


def list_windows():
    root = _dpy().screen().root
    ids = _prop(root, "_NET_CLIENT_LIST") or []
    windows = []
    for wid in ids:
        win = _dpy().create_resource_object("window", wid)
        try:
            title = _title(win)
            geometry = win.get_geometry()
            if title and geometry.width > 0 and geometry.height > 0 \
                    and _atom("_NET_WM_STATE_HIDDEN") not in _states(win):
                windows.append(Window(wid, title, geometry.width, geometry.height))
        except Exception:
            continue    # window vanished while we were looking
    return windows


def arrange(window, monitor, layout="center"):
    win = _resolve(window)
    states = _states(win)
    if _atom("_NET_WM_STATE_HIDDEN") in states:
        _activate(win)
    if _atom("_NET_WM_STATE_MAXIMIZED_VERT") in states or _atom("_NET_WM_STATE_MAXIMIZED_HORZ") in states:
        _set_state(win, _REMOVE, "_NET_WM_STATE_MAXIMIZED_VERT", "_NET_WM_STATE_MAXIMIZED_HORZ")
        _dpy().sync()
        time.sleep(0.1)    # let the window manager un-maximize before we move it

    geometry = win.get_geometry()
    p = compute_placement(monitor, layout, geometry.width, geometry.height)
    flags = _FROM_PAGER | _X | _Y
    width = height = 0
    if p.width is not None:
        flags |= _W | _H
        width, height = p.width, p.height
    _send(win, "_NET_MOVERESIZE_WINDOW", [flags, p.x, p.y, width, height])
    if p.maximize:
        _dpy().sync()
        time.sleep(0.1)    # maximize on the monitor the window has just moved to
        _set_state(win, _ADD, "_NET_WM_STATE_MAXIMIZED_VERT", "_NET_WM_STATE_MAXIMIZED_HORZ")
    _dpy().flush()


def zoom(window, action):
    """Send Ctrl+= / Ctrl+- / Ctrl+0 to the window through the XTEST extension."""
    win = _resolve(window)
    _activate(win)
    _dpy().sync()
    time.sleep(0.2)

    dpy = _dpy()
    ctrl = dpy.keysym_to_keycode(XK.string_to_keysym("Control_L"))
    key = dpy.keysym_to_keycode(XK.string_to_keysym(_ZOOM_KEYSYMS[action]))
    for event_type, keycode in ((X.KeyPress, ctrl), (X.KeyPress, key), (X.KeyRelease, key), (X.KeyRelease, ctrl)):
        xtest.fake_input(dpy, event_type, keycode)
    dpy.sync()

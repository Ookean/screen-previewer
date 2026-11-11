"""Send Ctrl+Plus / Ctrl+Minus / Ctrl+0 through the desktop's "remote desktop" portal.

The portal shows a permission dialog the first time. All D-Bus work happens in one background thread, so a
dialog that waits for an answer never freezes the window.
"""
import queue
import threading
import time

from ..portal import Portal, new_token

_CONTROL = 0xFFE3                                          # XK_Control_L
_KEYSYMS = {"in": 0x3D, "out": 0x2D, "reset": 0x30}        # '=' (Ctrl+= zooms in on most layouts), '-', '0'
_PRESS, _RELEASE = 1, 0


class ZoomKeys:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = None

    def send(self, action):
        self._queue.put(action)
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self):
        try:
            portal = Portal()
            session = portal.request("RemoteDesktop", "CreateSession", "a{sv}",
                                     lambda o: (dict(o, session_handle_token=("s", new_token())),))["session_handle"][1]
            portal.request("RemoteDesktop", "SelectDevices", "oa{sv}", lambda o: (session, dict(o, types=("u", 1))))
            portal.request("RemoteDesktop", "Start", "osa{sv}", lambda o: (session, "", o))
            while True:
                key = _KEYSYMS[self._queue.get()]
                time.sleep(0.2)                           # give the window a moment to take the focus
                for keysym, state in ((_CONTROL, _PRESS), (key, _PRESS), (key, _RELEASE), (_CONTROL, _RELEASE)):
                    portal.call("RemoteDesktop", "NotifyKeyboardKeysym", "oa{sv}iu", (session, {}, keysym, state))
        except Exception as e:
            print(f"Zoom key error: {e}")     # the thread ends; the next zoom click starts a new one

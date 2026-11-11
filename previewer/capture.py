"""Where the preview's pixels come from.

MssCapture      Windows and X11: reads the screen directly (mss).
PortalCapture   Wayland: asks the desktop for permission through xdg-desktop-portal, then reads the
                PipeWire stream it grants with GStreamer's `gst-launch-1.0` (the user's system needs
                GStreamer's PipeWire plugin, which most Wayland desktops already have).

Both give a list of mss-style monitor dicts and a `grab(monitor)` that returns a PIL image or None.
"""
import subprocess
import threading

import mss
from PIL import Image

from .config import ON_WAYLAND
from .portal import Portal, new_token


class MssCapture:
    def __init__(self):
        self._sct = mss.mss()

    def monitors(self):
        return self._sct.monitors[1:]   # index 0 = combined virtual screen

    def grab(self, monitor):
        shot = self._sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

    def status(self):
        return None

    def close(self):
        self._sct.close()


class PortalCapture:
    """One screen, chosen by the user in the desktop's own dialog (the portal decides which)."""

    FPS = 10

    def __init__(self):
        self.size = None            # (width, height) once the stream is running
        self._error = None
        self._frame = None
        self._lock = threading.Lock()
        self._proc = None
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def monitors(self):
        width, height = self.size or (0, 0)     # 0x0 = still waiting for the permission dialog
        return [{"left": 0, "top": 0, "width": width, "height": height}]

    def grab(self, monitor):
        with self._lock:
            return self._frame

    def status(self):
        """(locale key, values) to show instead of a picture, or None."""
        if self._error:
            return "preview.wayland_error", {"error": self._error}
        if self._frame is None:
            return "preview.wayland_waiting", {}
        return None

    def close(self):
        self._stop.set()
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()

    # ------------------------------------------------------------------ background thread
    def _run(self):
        try:
            node, fd, size = _open_screencast()
            self.size = size
            self._read_frames(node, fd, size)
        except Exception as e:
            if not self._stop.is_set():
                self._error = str(e) or type(e).__name__
                print(f"Wayland capture error: {self._error}")

    def _read_frames(self, node, fd, size):
        width, height = size
        caps = f"video/x-raw,format=RGBx,width={width},height={height},framerate={self.FPS}/1"
        command = ["gst-launch-1.0", "-q", "pipewiresrc", f"fd={fd}", f"path={node}", "!", "videorate", "!",
                   "videoconvert", "!", "videoscale", "!", caps, "!", "fdsink", "fd=1"]
        try:
            self._proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                          pass_fds=(fd,))
        except FileNotFoundError:
            raise RuntimeError("gst-launch-1.0 not found: install GStreamer and its PipeWire plugin")

        frame_size = width * height * 4
        while not self._stop.is_set():
            data = self._proc.stdout.read(frame_size)
            if len(data) < frame_size:
                raise RuntimeError("the screen stream ended (is GStreamer's PipeWire plugin installed?)")
            image = Image.frombytes("RGB", (width, height), data, "raw", "RGBX")
            with self._lock:
                self._frame = image


# ---------------------------------------------------------------------- xdg-desktop-portal ScreenCast
def _open_screencast():
    """Ask for a screen, return (PipeWire node id, PipeWire fd, (width, height)). Blocks until the user answers."""
    portal = Portal()
    session = portal.request("ScreenCast", "CreateSession", "a{sv}",
                             lambda o: (dict(o, session_handle_token=("s", new_token())),))["session_handle"][1]
    portal.request("ScreenCast", "SelectSources", "oa{sv}",
                   lambda o: (session, dict(o, types=("u", 1), multiple=("b", False), cursor_mode=("u", 2))))
    streams = portal.request("ScreenCast", "Start", "osa{sv}", lambda o: (session, "", o))["streams"][1]
    if not streams:
        raise RuntimeError("no screen was shared")
    node, properties = streams[0]
    size = properties["size"][1] if "size" in properties else (1920, 1080)

    reply = portal.call("ScreenCast", "OpenPipeWireRemote", "oa{sv}", (session, {}))
    return node, reply.body[0].to_raw_fd(), tuple(size)


def make_capture():
    return PortalCapture() if ON_WAYLAND else MssCapture()

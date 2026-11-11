"""Window control on Hyprland through `hyprctl`, which ships with Hyprland."""
import json
import re
import shutil
import subprocess

from .common import Window

_ADDRESS = re.compile(r"0x[0-9a-f]+")


def usable():
    return shutil.which("hyprctl") is not None


def _ctl(*args):
    return subprocess.run(["hyprctl", *args], capture_output=True, text=True, timeout=5, check=True).stdout


def monitors():
    result = []
    for m in json.loads(_ctl("monitors", "-j")):
        scale = m.get("scale") or 1
        result.append({"left": m["x"], "top": m["y"],
                       "width": round(m["width"] / scale), "height": round(m["height"] / scale)})   # logical pixels
    return result


def windows():
    return [Window(c["address"], c["title"], c["size"][0], c["size"][1])
            for c in json.loads(_ctl("clients", "-j"))
            if c.get("mapped") and not c.get("hidden") and c.get("title")]


def _address(window):
    if not _ADDRESS.fullmatch(str(window.id)):
        raise ValueError(f"unexpected window address {window.id!r}")
    return f"address:{window.id}"


def place(window, p):
    target = _address(window)
    commands = [f"dispatch setfloating {target}"]
    if p.width is not None:
        commands.append(f"dispatch resizewindowpixel exact {p.width} {p.height},{target}")
    commands.append(f"dispatch movewindowpixel exact {p.x} {p.y},{target}")
    if p.maximize:
        commands += [f"dispatch focuswindow {target}", "dispatch fullscreen 1"]
    _ctl("--batch", " ; ".join(commands))


def focus(window):
    _ctl("dispatch", "focuswindow", _address(window))

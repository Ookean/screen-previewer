"""Window control on Sway through `swaymsg`, which ships with Sway."""
import json
import shutil
import subprocess

from .common import Window


def usable():
    return shutil.which("swaymsg") is not None


def _msg(*args):
    return subprocess.run(["swaymsg", *args], capture_output=True, text=True, timeout=5, check=True).stdout


def monitors():
    outputs = json.loads(_msg("-t", "get_outputs", "-r"))
    return [{"left": o["rect"]["x"], "top": o["rect"]["y"], "width": o["rect"]["width"], "height": o["rect"]["height"]}
            for o in outputs if o.get("active")]


def windows():
    found = []

    def walk(node):
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            if child.get("pid") and child.get("name"):          # a real application window, not a container
                found.append(Window(child["id"], child["name"], child["rect"]["width"], child["rect"]["height"]))
            walk(child)

    walk(json.loads(_msg("-t", "get_tree", "-r")))
    return found


def place(window, p):
    """Sway tiles windows, so a window is made floating first, then sized and moved to absolute coordinates."""
    sel = f"[con_id={int(window.id)}]"
    commands = [f"{sel} fullscreen disable", f"{sel} floating enable"]
    if p.width is not None:
        commands.append(f"{sel} resize set {p.width} {p.height}")
    commands.append(f"{sel} move absolute position {p.x} {p.y}")
    if p.maximize:
        commands.append(f"{sel} fullscreen enable")
    _msg("; ".join(commands))


def focus(window):
    _msg(f"[con_id={int(window.id)}] focus")

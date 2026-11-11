"""Window control on KDE Plasma by running small scripts inside KWin, the Plasma window manager.

KWin has no "move that window" call, but it can run a JavaScript file we give it. To get answers back, the script
calls a method on our own D-Bus connection. Nothing needs installing: this is KDE's normal scripting interface.
Written for Plasma 6, with fallbacks for Plasma 5 names.
"""
import json
import os
import tempfile
import uuid

from .common import Window

_HELPERS = """
function allWindows() { return typeof workspace.windowList === 'function' ? workspace.windowList() : workspace.clientList(); }
function setActive(w) { if (workspace.activeWindow !== undefined) workspace.activeWindow = w; else workspace.activeClient = w; }
function findWindow(id) {
  var list = allWindows();
  for (var i = 0; i < list.length; i++) { if (String(list[i].internalId) === id) return list[i]; }
  return null;
}
"""

_LIST = _HELPERS + """
var out = {windows: [], screens: []};
var list = allWindows();
for (var i = 0; i < list.length; i++) {
  var w = list[i];
  if (!w.normalWindow) continue;
  var g = w.frameGeometry;
  out.windows.push({id: String(w.internalId), title: String(w.caption), w: g.width, h: g.height});
}
if (workspace.screens) {
  for (var i = 0; i < workspace.screens.length; i++) { var g = workspace.screens[i].geometry; out.screens.push({x: g.x, y: g.y, w: g.width, h: g.height}); }
} else {
  for (var i = 0; i < workspace.numScreens; i++) { var g = workspace.clientArea(KWin.FullScreenArea, i, workspace.currentDesktop); out.screens.push({x: g.x, y: g.y, w: g.width, h: g.height}); }
}
callDBus("__DEST__", "/screenpreview", "org.screenpreview.Receiver", "Report", JSON.stringify(out));
"""

_ACT = _HELPERS + """
var args = __ARGS__;
var w = findWindow(args.id);
if (w) {
  if (w.minimized) w.minimized = false;
  if (args.place) {
    w.setMaximize(false, false);
    var g = w.frameGeometry;
    g.x = args.x; g.y = args.y;
    if (args.w) { g.width = args.w; g.height = args.h; }
    w.frameGeometry = g;
    if (args.maximize) w.setMaximize(true, true);
  }
  if (args.focus) setActive(w);
}
"""


def usable():
    try:
        import jeepney  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS")) or os.path.exists(f"/run/user/{os.getuid()}/bus")


def _run_script(source, expect_report=False):
    """Load `source` into KWin and run it. If `expect_report`, wait for the script's reply and return it (a str)."""
    from jeepney import DBusAddress, MatchRule, MessageType, new_method_call, new_method_return
    from jeepney.io.blocking import open_dbus_connection

    conn = open_dbus_connection(bus="SESSION")
    kwin = DBusAddress("/Scripting", bus_name="org.kde.KWin", interface="org.kde.kwin.Scripting")
    name = "screenpreview-" + uuid.uuid4().hex[:12]
    handle, path = tempfile.mkstemp(suffix=".js", prefix="screenpreview-")
    with os.fdopen(handle, "w", encoding="utf-8") as f:
        f.write(source.replace("__DEST__", conn.unique_name))
    loaded = False
    try:
        rule = MatchRule(type="method_call", path="/screenpreview")
        with conn.filter(rule) as incoming:
            script_id = conn.send_and_get_reply(new_method_call(kwin, "loadScript", "ss", (path, name))).body[0]
            if script_id < 0:
                raise RuntimeError("KWin did not accept the script")
            loaded = True
            for object_path in (f"/Scripting/Script{script_id}", f"/{script_id}"):   # Plasma 6, then Plasma 5
                script = DBusAddress(object_path, bus_name="org.kde.KWin", interface="org.kde.kwin.Script")
                if conn.send_and_get_reply(new_method_call(script, "run")).header.message_type != MessageType.error:
                    break
            else:
                raise RuntimeError("KWin could not run the script")

            if not expect_report:
                return None
            call = conn.recv_until_filtered(incoming, timeout=5)
            send = getattr(conn, "send_message", None) or conn.send
            send(new_method_return(call))
            return call.body[0]
    finally:
        if loaded:
            try:
                conn.send_and_get_reply(new_method_call(kwin, "unloadScript", "s", (name,)))
            except Exception:
                pass
        os.remove(path)
        conn.close()


def _report():
    return json.loads(_run_script(_LIST, expect_report=True))


def monitors():
    return [{"left": s["x"], "top": s["y"], "width": s["w"], "height": s["h"]} for s in _report()["screens"]]


def windows():
    return [Window(w["id"], w["title"], w["w"], w["h"]) for w in _report()["windows"] if w["title"].strip()]


def _act(**args):
    _run_script(_ACT.replace("__ARGS__", json.dumps(args)))


def place(window, p):
    _act(id=window.id, place=True, x=p.x, y=p.y, w=p.width, h=p.height, maximize=p.maximize)


def focus(window):
    _act(id=window.id, focus=True)

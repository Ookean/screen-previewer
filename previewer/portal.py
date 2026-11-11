"""A small helper for talking to xdg-desktop-portal over D-Bus (jeepney).

The portal is the desktop's own permission broker. Screen capture and key presses on Wayland go through it:
the desktop shows a dialog, the user answers, and only then does the app get access.
"""
import uuid

_BUS_NAME = "org.freedesktop.portal.Desktop"
_PATH = "/org/freedesktop/portal/desktop"
DIALOG_TIMEOUT = 300   # seconds the user has to answer a permission dialog


def new_token():
    return "sp" + uuid.uuid4().hex[:12]


class Portal:
    """One D-Bus connection to the portal. Not thread-safe: use it from one thread."""

    def __init__(self):
        from jeepney.io.blocking import open_dbus_connection
        self.conn = open_dbus_connection(bus="SESSION", enable_fds=True)
        self._sender = self.conn.unique_name.lstrip(":").replace(".", "_")

    def _address(self, interface):
        from jeepney import DBusAddress
        return DBusAddress(_PATH, bus_name=_BUS_NAME, interface=f"org.freedesktop.portal.{interface}")

    def call(self, interface, method, signature, body):
        """A plain method call. Returns the reply message."""
        from jeepney import new_method_call
        return self.conn.send_and_get_reply(new_method_call(self._address(interface), method, signature, body))

    def request(self, interface, method, signature, make_body):
        """Call a method that answers later through a Request/Response signal, and return its results dict.

        `make_body(options)` gets the options dict (already holding our handle_token) and returns the call's body.
        """
        from jeepney import MatchRule
        from jeepney.bus_messages import message_bus
        from jeepney.io.blocking import Proxy

        token = new_token()
        path = f"{_PATH}/request/{self._sender}/{token}"
        rule = MatchRule(type="signal", interface="org.freedesktop.portal.Request", member="Response", path=path)
        Proxy(message_bus, self.conn).AddMatch(rule)     # listen before calling, so the answer cannot be missed
        with self.conn.filter(rule) as answers:
            self.call(interface, method, signature, make_body({"handle_token": ("s", token)}))
            reply = self.conn.recv_until_filtered(answers, timeout=DIALOG_TIMEOUT)
        code, results = reply.body
        if code != 0:
            raise RuntimeError("permission was not given" if code == 1 else f"portal error {code}")
        return results

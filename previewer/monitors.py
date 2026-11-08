"""Monitor discovery and selection, independent of any widgets."""
from .capture import make_capture
from .i18n import t


def describe_monitor(index, monitor):
    if monitor["width"] <= 0:   # Wayland: the screen is only known once the user has allowed sharing
        return t("monitor.wayland_pending")
    return f"{index}: {monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']})"


class MonitorModel:
    """The monitors the capture can see, and which one is selected (1-based, like mss)."""

    def __init__(self, capture=None):
        self.capture = capture or make_capture()
        self.monitors = []
        self.index = None

    @property
    def current(self):
        return None if self.index is None else self.monitors[self.index - 1]

    def labels(self):
        return [describe_monitor(i, m) for i, m in enumerate(self.monitors, start=1)]

    def refresh(self):
        """Re-read the monitors and keep the selection valid. Returns False if none were found."""
        self.monitors = self.capture.monitors()
        if not self.monitors:
            self.index = None
            return False

        if self.index is None or not 1 <= self.index <= len(self.monitors):
            self.index = 2 if len(self.monitors) > 1 else 1   # usually the extended screen
        return True

    def select(self, index):
        self.index = index

    def close(self):
        self.capture.close()

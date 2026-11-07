"""Monitor discovery and selection, independent of any widgets."""
import mss


def describe_monitor(index, monitor):
    return f"{index}: {monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']})"


class MonitorModel:
    """The monitors mss can see, and which one is selected (1-based, like mss)."""

    def __init__(self):
        self.sct = mss.mss()
        self.monitors = []
        self.index = None

    @property
    def current(self):
        return None if self.index is None else self.monitors[self.index - 1]

    def labels(self):
        return [describe_monitor(i, m) for i, m in enumerate(self.monitors, start=1)]

    def refresh(self):
        """Re-read the monitors and keep the selection valid. Returns False if none were found."""
        self.monitors = self.sct.monitors[1:]  # index 0 = combined virtual screen
        if not self.monitors:
            self.index = None
            return False

        if self.index is None or not 1 <= self.index <= len(self.monitors):
            self.index = 2 if len(self.monitors) > 1 else 1   # usually the extended screen
        return True

    def select(self, index):
        self.index = index

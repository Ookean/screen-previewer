"""Feature: choose which monitor windows are moved to (and which one is previewed, on Windows and X11)."""
from PySide6.QtCore import Signal

from ..i18n import t
from ..widgets import Card, PopupComboBox


class MonitorPanel(Card):
    changed = Signal()      # the selected monitor (or the monitor list) changed

    def __init__(self, model):
        super().__init__(t("section.monitor"))
        self.model = model
        self.combo = PopupComboBox(on_popup=self.refresh)
        self.combo.activated.connect(self._on_selected)
        self.body.addWidget(self.combo)

    def refresh(self):
        if not self.model.refresh():
            print("No monitors detected.")
            return
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self.model.labels())
        self.combo.setCurrentIndex(self.model.index - 1)
        self.combo.blockSignals(False)
        self.changed.emit()

    def _on_selected(self, position):
        self.model.select(position + 1)
        self.changed.emit()

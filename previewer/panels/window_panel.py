"""Everything that acts on one chosen window: pick it, move it, arrange it, zoom it."""
from PySide6.QtCore import QSize, QTimer, Signal
from PySide6.QtWidgets import (QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
                               QVBoxLayout, QWidget)

from .. import theme, window_control
from ..about import open_desktop_issue
from ..config import desktop_info
from ..i18n import t
from ..icons import layout_icon
from ..widgets import Card, PopupComboBox


class WindowPanel(QWidget):
    """Three cards that all work on the window selected in the first one.

    Window: the picker and "Move to Monitor". Layout: the layout tiles and "Apply layout".
    Zoom: the zoom buttons. Moving and layouts go to the monitor selected in `model` (a MonitorModel).
    """

    message = Signal(str)       # a short result for the status bar
    ZOOM_BUTTONS = (("−", "out"), ("+", "in"), ("100%", "reset"))
    REFOCUS_MS = 300            # let the other window receive its keys before we take the focus back

    def __init__(self, model, on_action_done=None, exclude=None):
        """`on_action_done()` is called shortly after a move or zoom (the app uses it to take the focus back).
        `exclude(window)` returns True for windows that must not be offered (the app's own window).
        """
        super().__init__()
        self.model = model
        self.on_action_done = on_action_done
        self.exclude = exclude
        self.windows = []

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(12)

        # Window: pick one and send it to the selected monitor
        picker = Card(t("section.window"))
        self.window_combo = PopupComboBox(on_popup=self.refresh)
        picker.body.addWidget(self.window_combo)
        self.move_btn = QPushButton(t("window.move"))
        self.move_btn.setObjectName("primary")
        self.move_btn.clicked.connect(lambda *_: self.move_to_monitor())
        picker.body.addWidget(self.move_btn)
        column.addWidget(picker)

        # Layout: choose where the window goes, then apply
        arrange = Card(t("section.layout"))
        grid = QGridLayout()
        grid.setSpacing(8)
        self._tile_group = QButtonGroup(self)
        self._tile_group.setExclusive(True)
        self.tiles = []
        color = theme.colors()["text"]
        for position, layout in enumerate(window_control.LAYOUTS):
            tile = QToolButton()
            tile.setObjectName("layoutTile")
            tile.setCheckable(True)
            tile.setIcon(layout_icon(layout, color))
            tile.setIconSize(QSize(34, 34))
            tile.setToolTip(t(f"layout.{layout}"))
            tile.setFixedHeight(46)
            self._tile_group.addButton(tile, position)
            grid.addWidget(tile, position // 3, position % 3)
            self.tiles.append(tile)
        self.tiles[0].setChecked(True)
        self._tile_group.idClicked.connect(self._on_tile)
        arrange.body.addLayout(grid)
        self.layout_caption = QLabel(t(f"layout.{window_control.LAYOUTS[0]}"))
        self.layout_caption.setObjectName("muted")
        arrange.body.addWidget(self.layout_caption)
        self.apply_btn = QPushButton(t("layout.apply"))
        self.apply_btn.clicked.connect(lambda *_: self.apply_layout())
        arrange.body.addWidget(self.apply_btn)
        column.addWidget(arrange)

        # Zoom
        zoom_card = Card(t("section.zoom"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.zoom_btns = []
        for text, action in self.ZOOM_BUTTONS:
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, a=action: self.zoom(a))
            row.addWidget(button)
            self.zoom_btns.append(button)
        zoom_card.body.addLayout(row)
        column.addWidget(zoom_card)

        self.controls = [self.window_combo, self.move_btn, *self.tiles, self.apply_btn, *self.zoom_btns]
        if not window_control.AVAILABLE:
            for control in self.controls[:-len(self.zoom_btns)]:
                control.setEnabled(False)
            self.window_combo.setPlaceholderText(t(window_control.UNAVAILABLE_REASON))
        if not window_control.ZOOM_AVAILABLE:
            for button in self.zoom_btns:
                button.setEnabled(False)

        # A Wayland desktop we have no backend for: ask the user to tell us which one it is.
        if window_control.NEEDS_SUPPORT_REPORT:
            hint = Card()
            text = QLabel(t("window.hint_report", desktop=desktop_info()))
            text.setObjectName("hint")
            text.setWordWrap(True)
            hint.body.addWidget(text)
            report = QPushButton(t("window.report_desktop"))
            report.clicked.connect(lambda *_: open_desktop_issue())
            hint.body.addWidget(report)
            column.addWidget(hint)

    # ------------------------------------------------------------------ window list
    def refresh(self):
        """Reload the list of open windows, keeping the selected one selected if it is still open."""
        if not window_control.AVAILABLE:
            return
        previous = self.selected_window()
        previous_key = None if previous is None else window_control.window_key(previous)
        try:
            self.windows = [w for w in window_control.list_windows() if not (self.exclude and self.exclude(w))]
            keys = [window_control.window_key(w) for w in self.windows]
            labels = [f"{w.title} ({w.width}x{w.height})" for w in self.windows]
        except Exception as e:
            print(f"Window list error: {e}")
            self.windows, keys, labels = [], [], []

        self.window_combo.blockSignals(True)
        try:
            self.window_combo.clear()
            self.window_combo.addItems(labels)
            self.window_combo.setCurrentIndex(keys.index(previous_key) if previous_key in keys else (0 if keys else -1))
        finally:
            self.window_combo.blockSignals(False)
        if not self.windows:
            self.window_combo.setPlaceholderText(t("window.none_found"))

    def selected_window(self):
        idx = self.window_combo.currentIndex()
        return self.windows[idx] if 0 <= idx < len(self.windows) else None

    # ------------------------------------------------------------------ actions
    def move_to_monitor(self):
        """Move the window to the selected monitor, centered, keeping its size."""
        window = self.selected_window()
        if window is not None:
            self._arrange(window, "center", t("status.moved", title=window.title, index=self.model.index))

    def apply_layout(self):
        """Arrange the window on the selected monitor using the chosen layout."""
        layout = window_control.LAYOUTS[max(self._tile_group.checkedId(), 0)]
        self._arrange(self.selected_window(), layout, t("status.layout_applied", layout=t(f"layout.{layout}")))

    def zoom(self, action):
        window = self.selected_window()
        if window is None:
            return
        try:
            window_control.zoom(window, action)
            self.message.emit(t("status.zoomed", title=window.title))
        except Exception as e:
            print(f"Zoom error: {e}")
            self.message.emit(t("status.failed", error=e))
        self._action_done()

    def _arrange(self, window, layout, done_message):
        monitor = self.model.current
        if window is None or monitor is None:
            return
        try:
            window_control.arrange(window, monitor, layout)
            self.message.emit(done_message)
        except Exception as e:
            print(f"Arrange error: {e}")
            self.message.emit(t("status.failed", error=e))
        self._action_done()

    def _action_done(self):
        if self.on_action_done is not None:
            QTimer.singleShot(self.REFOCUS_MS, self.on_action_done)

    def _on_tile(self, position):
        self.layout_caption.setText(t(f"layout.{window_control.LAYOUTS[position]}"))

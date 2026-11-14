"""Main window: a sidebar of control cards next to the live preview. Rebuilds itself on language or theme changes."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QMainWindow, QScrollArea, QVBoxLayout, QWidget)

from . import i18n, theme, window_control
from .i18n import t
from .menubar import build_menus
from .monitors import MonitorModel
from .panels.monitor_panel import MonitorPanel
from .panels.preview_panel import PreviewPanel
from .panels.window_panel import WindowPanel

SIDEBAR_WIDTH = 316


class ScreenPreviewApp(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.model = MonitorModel(monitor_source=window_control.list_monitors)   # selected monitor, shared by the panels
        self.resize(1120, 700)
        self.setMinimumSize(760, 520)
        self._build()

    def _build(self):
        """Create the menus and all panels. Runs at startup and again after a language or theme change."""
        build_menus(self, self.settings, self.on_language_chosen, self.on_theme_chosen)
        self.setWindowTitle(t("app.title"))

        self.monitor_panel = MonitorPanel(self.model)
        self.monitor_panel.changed.connect(self.on_monitor_changed)
        self.window_panel = WindowPanel(self.model, on_action_done=self.restore_focus, exclude=self.is_own_window)
        self.window_panel.message.connect(lambda text: self.statusBar().showMessage(text, 5000))

        controls = QWidget()
        controls.setObjectName("sidebar")
        column = QVBoxLayout(controls)
        column.setContentsMargins(0, 0, 4, 0)
        column.setSpacing(12)
        column.addWidget(self.monitor_panel)
        column.addWidget(self.window_panel)
        column.addStretch(1)

        sidebar = QScrollArea()          # scrolls on a short window instead of squashing the controls
        sidebar.setWidgetResizable(True)
        sidebar.setFrameShape(QFrame.Shape.NoFrame)
        sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setWidget(controls)

        self.preview = PreviewPanel(self.model)
        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(12, 8, 12, 4)
        row.setSpacing(12)
        row.addWidget(sidebar)
        row.addWidget(self.preview, 1)
        self.setCentralWidget(central)   # Qt deletes the previous central widget, and with it the old panels

        self.monitor_panel.refresh()
        self.window_panel.refresh()
        self.preview.start()

    # ------------------------------------------------------------------ settings changes
    def on_language_chosen(self, preference):
        """Called from the Language menu with "system" or a language code."""
        self.settings.set_language(preference)
        i18n.set_language(preference)
        # Rebuild after the menu command has returned: deleting a menu from inside its own handler is unsafe.
        QTimer.singleShot(0, self._build)

    def on_theme_chosen(self, preference):
        """Called from the Appearance menu with "system", "light" or "dark"."""
        self.settings.set_theme(preference)
        theme.apply(QApplication.instance(), preference)
        QTimer.singleShot(0, self._build)      # the layout icons are drawn in the theme's colour

    def follow_system_theme(self):
        """Switch along when the operating system changes between light and dark (if the user chose "system")."""
        def changed(*_):
            if self.settings.theme == theme.SYSTEM:
                self.on_theme_chosen(theme.SYSTEM)
        QApplication.instance().styleHints().colorSchemeChanged.connect(changed)

    # ------------------------------------------------------------------ events
    def on_monitor_changed(self):
        monitor = self.model.current
        if monitor["width"] <= 0:     # Wayland: size unknown until the user has allowed sharing
            self.setWindowTitle(t("app.title"))
            return
        self.setWindowTitle(t("app.title_monitor", index=self.model.index,
                              width=monitor["width"], height=monitor["height"]))

    def is_own_window(self, window):
        """True for this app's own window, so it is not offered in the window list.

        Windows and X11 identify it by its native handle. Wayland gives no handle to compare, so the title is used too.
        """
        return window_control.window_key(window) == int(self.winId()) or window.title == self.windowTitle()

    def restore_focus(self):
        """Moving or zooming another window activates it; take the focus back so the next click lands here."""
        try:
            window_control.focus_own_window(int(self.winId()))
        except Exception as e:
            print(f"Focus error: {e}")

    def closeEvent(self, event):
        self.model.close()
        super().closeEvent(event)

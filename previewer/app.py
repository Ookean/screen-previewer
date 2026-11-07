"""Main window: assembles the menu bar and the panels, and rebuilds them when the language changes."""
import tkinter as tk

from . import i18n
from .config import resource_path
from .i18n import t
from .menubar import build_menubar
from .monitors import MonitorModel
from .panels.monitor_panel import MonitorPanel
from .panels.preview_panel import PreviewPanel
from .panels.window_panel import WindowPanel


class ScreenPreviewApp:
    def __init__(self, root, settings):
        self.root = root
        self.settings = settings
        self.model = MonitorModel()   # which monitor is selected; shared by the panels

        try:
            # default=... also gives the About window the same icon
            root.iconbitmap(default=resource_path("Assets/icon.ico"))
        except tk.TclError:
            pass  # icon missing or not a valid .ico: keep Tk's default

        root.geometry("900x600")
        root.minsize(280, 240)
        self._build()

    def _build(self):
        """Create the menu bar and all panels. Runs at startup and again after a language change."""
        old_widgets = self.root.winfo_children()

        build_menubar(self.root, self.settings, self.on_language_chosen)
        self.root.title(t("app.title"))

        self.monitor_panel = MonitorPanel(self.root, self.model, on_change=self.on_monitor_changed)
        self.monitor_panel.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(6, 3))

        self.window_panel = WindowPanel(self.root, self.model)
        self.window_panel.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 6))

        self.preview = PreviewPanel(self.root, self.model)
        self.preview.pack(fill=tk.BOTH, expand=True)

        # The old widgets go only now, after the new menu bar is attached, so the window
        # never points at a destroyed menu. This also closes an open About window.
        for widget in old_widgets:
            widget.destroy()

        self.monitor_panel.refresh()
        self.window_panel.refresh()
        self.preview.start()

    def on_language_chosen(self, preference):
        """Called from the Language menu with "system" or a language code."""
        self.settings.set_language(preference)
        i18n.set_language(preference)
        # Rebuild once the menu command has returned: destroying a menu from inside its own callback is unsafe.
        self.root.after_idle(self._build)

    def on_monitor_changed(self):
        monitor = self.model.current
        self.root.title(t("app.title_monitor", index=self.model.index,
                          width=monitor["width"], height=monitor["height"]))

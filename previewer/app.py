"""Main window: assembles the menu bar and the panels."""
import tkinter as tk

from .config import resource_path
from .menubar import build_menubar
from .monitors import MonitorModel
from .panels.monitor_panel import MonitorPanel
from .panels.preview_panel import PreviewPanel
from .panels.window_panel import WindowPanel


class ScreenPreviewApp:
    def __init__(self, root):
        self.root = root
        self.model = MonitorModel()   # which monitor is selected; shared by the panels below

        try:
            # default=... also gives the About window the same icon
            root.iconbitmap(default=resource_path("Assets/icon.ico"))
        except tk.TclError:
            pass  # icon missing or not a valid .ico: keep Tk's default

        build_menubar(root)
        root.title("Monitor Preview")
        root.geometry("900x600")
        root.minsize(280, 240)

        self.monitor_panel = MonitorPanel(root, self.model, on_change=self.on_monitor_changed)
        self.monitor_panel.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(6, 3))

        self.window_panel = WindowPanel(root, self.model)
        self.window_panel.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 6))

        self.preview = PreviewPanel(root, self.model)
        self.preview.pack(fill=tk.BOTH, expand=True)

        self.monitor_panel.refresh()
        self.window_panel.refresh()
        self.preview.start()

    def on_monitor_changed(self):
        monitor = self.model.current
        self.root.title(f"Monitor {self.model.index} Preview  ({monitor['width']}x{monitor['height']})")
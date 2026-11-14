"""Everything that acts on one chosen window: pick it, move it, arrange it, zoom it."""
import tkinter as tk
from tkinter import ttk

from .. import window_control
from ..about import open_desktop_issue
from ..config import desktop_info
from ..i18n import t


class WindowPanel(tk.Frame):
    """Two rows of controls that all work on the window selected in the picker.

    Row 1: the window picker, a refresh button and "Move to Monitor".
    Row 2: the layout dropdown with "Apply layout", and the zoom buttons.

    Moving and layouts go to the monitor currently selected in `model` (a MonitorModel).
    """

    ZOOM_BUTTONS = (("−", "out"), ("+", "in"), ("100%", "reset"))
    REFOCUS_MS = 300   # let the other window receive its keys before we take the focus back

    def __init__(self, parent, model, on_action_done=None):
        """`on_action_done()` is called shortly after a move or zoom (the app uses it to take the focus back)."""
        super().__init__(parent)
        self.model = model
        self.on_action_done = on_action_done
        self.windows = []

        # Row 1: pick a window and send it to the selected monitor
        picker = tk.Frame(self)
        picker.pack(side=tk.TOP, fill=tk.X, pady=(0, 3))

        tk.Label(picker, text=t("window.label")).pack(side=tk.LEFT, padx=(0, 6))
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(picker, textvariable=self.window_var, state="readonly", width=40)
        self.window_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        refresh_btn = tk.Button(picker, text=t("common.refresh"), command=self.refresh)
        refresh_btn.pack(side=tk.LEFT, padx=(6, 0))
        move_btn = tk.Button(picker, text=t("window.move"), command=self.move_to_monitor)
        move_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Row 2: arrange it and zoom it
        options = tk.Frame(self)
        options.pack(side=tk.TOP, fill=tk.X)

        tk.Label(options, text=t("layout.label")).pack(side=tk.LEFT, padx=(0, 6))
        layout_labels = [t(f"layout.{layout}") for layout in window_control.LAYOUTS]
        self.layout_combo = ttk.Combobox(options, values=layout_labels, state="readonly",
                                         width=max(len(label) for label in layout_labels) + 1)
        self.layout_combo.current(0)
        self.layout_combo.pack(side=tk.LEFT)
        apply_btn = tk.Button(options, text=t("layout.apply"), command=self.apply_layout)
        apply_btn.pack(side=tk.LEFT, padx=(6, 0))

        tk.Label(options, text=t("zoom.label")).pack(side=tk.LEFT, padx=(16, 6))
        zoom_btns = [tk.Button(options, text=text, width=4, command=lambda a=action: self.zoom(a))
                     for text, action in self.ZOOM_BUTTONS]
        for btn in zoom_btns:
            btn.pack(side=tk.LEFT, padx=(0, 4))

        # Without pygetwindow/pywin32 none of the controls can work.
        self.controls = [self.window_combo, refresh_btn, move_btn, self.layout_combo, apply_btn, *zoom_btns]
        if not window_control.AVAILABLE:
            for control in self.controls[:5]:
                control.configure(state="disabled")
            self.window_var.set(t(window_control.UNAVAILABLE_REASON))
        if not window_control.ZOOM_AVAILABLE:
            for btn in zoom_btns:
                btn.configure(state="disabled")

        # A Wayland desktop we have no backend for: ask the user to tell us which one it is.
        if window_control.NEEDS_SUPPORT_REPORT:
            hint = tk.Frame(self)
            hint.pack(side=tk.TOP, fill=tk.X, pady=(3, 0))
            tk.Label(hint, text=t("window.hint_report", desktop=desktop_info()), wraplength=560,
                     justify=tk.LEFT).pack(side=tk.LEFT)
            tk.Button(hint, text=t("window.report_desktop"), command=open_desktop_issue).pack(side=tk.LEFT, padx=(6, 0))

    def refresh(self):
        """Reload the list of open windows."""
        if not window_control.AVAILABLE:
            return
        try:
            self.windows = window_control.list_windows()
        except Exception as e:
            print(f"Window list error: {e}")
            self.windows = []

        self.window_combo["values"] = [f"{w.title} ({w.width}x{w.height})" for w in self.windows]
        if self.windows:
            self.window_combo.current(0)
        else:
            self.window_var.set(t("window.none_found"))

    def selected_window(self):
        idx = self.window_combo.current()
        return self.windows[idx] if 0 <= idx < len(self.windows) else None

    def move_to_monitor(self):
        """Move the window to the selected monitor, centered, keeping its size."""
        self._arrange("center")

    def apply_layout(self):
        """Arrange the window on the selected monitor using the chosen layout."""
        self._arrange(window_control.LAYOUTS[max(self.layout_combo.current(), 0)])

    def zoom(self, action):
        window = self.selected_window()
        if window is None:
            return
        try:
            window_control.zoom(window, action)
        except Exception as e:
            print(f"Zoom error: {e}")
        self._action_done()

    def _arrange(self, layout):
        window, monitor = self.selected_window(), self.model.current
        if window is None or monitor is None:
            return
        try:
            window_control.arrange(window, monitor, layout)
        except Exception as e:
            print(f"Arrange error: {e}")
        self._action_done()

    def _action_done(self):
        if self.on_action_done is not None:
            self.after(self.REFOCUS_MS, self.on_action_done)

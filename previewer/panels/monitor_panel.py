"""Feature: choose which monitor to preview (and which one windows are moved to)."""
import tkinter as tk
from tkinter import ttk


class MonitorPanel(tk.Frame):
    def __init__(self, parent, model, on_change):
        super().__init__(parent)
        self.model = model
        self.on_change = on_change

        tk.Label(self, text="Monitor:").pack(side=tk.LEFT, padx=(0, 6))
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var, state="readonly", width=40)
        self.combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo.bind("<<ComboboxSelected>>", self._on_selected)

        tk.Button(self, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=(6, 0))

    def refresh(self):
        if not self.model.refresh():
            print("No monitors detected.")
            return
        self.combo["values"] = self.model.labels()
        self.combo.current(self.model.index - 1)
        self.on_change()

    def _on_selected(self, event=None):
        self.model.select(self.combo.current() + 1)
        self.on_change()
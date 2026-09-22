"""
Screen Preview Tool
-------------------
Live preview window for one of your monitors, with dropdowns to pick which
monitor to preview and to move any open window onto a chosen monitor.

Handy when a monitor is set to "Extend" and you can't see it directly
(e.g. a GM running a secondary display for players).

SETUP (one time):
    1. Install Python 3 from https://www.python.org/downloads/ (check "Add to PATH")
    2. pip install mss pillow pygetwindow pywin32

USAGE:
    python screen_preview.py
    python screen_preview.py --monitor 2   (preselect a monitor at launch)
    python screen_preview.py --list        (print monitor info and exit)

Window moving is Windows-only (uses pygetwindow + pywin32).
"""

import argparse
import sys

try:
    import mss
except ImportError:
    print("Missing dependency 'mss'. Install it with:  pip install mss pillow")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("Missing dependency 'Pillow'. Install it with:  pip install mss pillow")
    sys.exit(1)

try:
    import pygetwindow as gw
    HAVE_PYGETWINDOW = True
except ImportError:
    HAVE_PYGETWINDOW = False

import tkinter as tk
from tkinter import ttk


def list_monitors():
    with mss.mss() as sct:
        monitors = sct.monitors
        print("Detected monitors:")
        print(f"  index 0: ALL monitors combined ({monitors[0]['width']}x{monitors[0]['height']})")
        for i, m in enumerate(monitors[1:], start=1):
            print(f"  index {i}: {m['width']}x{m['height']} at position ({m['left']},{m['top']})")
        print("\nTip: index 1 is usually your primary/laptop screen, index 2 is usually the extended one.")


def get_open_windows():
    windows = []
    for w in gw.getAllWindows():
        if w.title.strip() and w.visible and w.width > 0 and w.height > 0:
            windows.append(w)
    return windows


def move_window_to_monitor(window, monitor):
    if window.isMinimized:
        window.restore()
    x = monitor["left"] + max(0, (monitor["width"] - window.width) // 2)
    y = monitor["top"] + max(0, (monitor["height"] - window.height) // 2)
    window.moveTo(x, y)


class ScreenPreviewApp:
    REFRESH_MS = 100  # ~10 fps

    def __init__(self, root, initial_monitor_index=None):
        self.root = root
        self.sct = mss.mss()
        self.tk_img = None

        self.root.title("Monitor Preview")
        self.root.geometry("900x600")
        self.root.minsize(280, 240)

        # Monitor selector row
        monitor_row = tk.Frame(root)
        monitor_row.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(6, 3))

        tk.Label(monitor_row, text="Monitor:").pack(side=tk.LEFT, padx=(0, 6))
        self.monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(monitor_row, textvariable=self.monitor_var, state="readonly", width=40)
        self.monitor_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_selected)

        tk.Button(monitor_row, text="Refresh", command=self.refresh_monitor_list).pack(side=tk.LEFT, padx=(6, 0))

        # Window selector row
        window_row = tk.Frame(root)
        window_row.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 6))

        tk.Label(window_row, text="Window:").pack(side=tk.LEFT, padx=(0, 6))
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(window_row, textvariable=self.window_var, state="readonly", width=40)
        self.window_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(window_row, text="Refresh", command=self.refresh_window_list).pack(side=tk.LEFT, padx=(6, 0))
        self.move_btn = tk.Button(window_row, text="Move to Monitor", command=self.move_selected_window)
        self.move_btn.pack(side=tk.LEFT, padx=(6, 0))

        if not HAVE_PYGETWINDOW:
            self.window_combo.configure(state="disabled")
            self.move_btn.configure(state="disabled")
            self.window_var.set("pygetwindow not installed (pip install pygetwindow pywin32)")

        # Preview area
        self.label = tk.Label(root, bg="black")
        self.label.pack(fill=tk.BOTH, expand=True)

        self.monitors = []
        self.monitor_index = None
        self.monitor = None
        self.windows = []

        self.refresh_monitor_list(preselect=initial_monitor_index)
        if HAVE_PYGETWINDOW:
            self.refresh_window_list()
        self.update_preview()

    def describe_monitor(self, i, m):
        return f"{i}: {m['width']}x{m['height']} at ({m['left']},{m['top']})"

    def refresh_monitor_list(self, preselect=None):
        all_monitors = self.sct.monitors  # index 0 = combined virtual screen
        self.monitors = all_monitors[1:]

        labels = [self.describe_monitor(i, m) for i, m in enumerate(self.monitors, start=1)]
        self.monitor_combo["values"] = labels
        if not labels:
            print("No monitors detected.")
            return

        if preselect is not None and 1 <= preselect <= len(self.monitors):
            new_index = preselect
        elif self.monitor_index is not None and 1 <= self.monitor_index <= len(self.monitors):
            new_index = self.monitor_index
        else:
            new_index = 2 if len(self.monitors) > 1 else 1

        self.monitor_index = new_index
        self.monitor = self.monitors[new_index - 1]
        self.monitor_combo.current(new_index - 1)
        self.root.title(f"Monitor {new_index} Preview  ({self.monitor['width']}x{self.monitor['height']})")

    def on_monitor_selected(self, event=None):
        selected = self.monitor_combo.current()
        self.monitor_index = selected + 1
        self.monitor = self.monitors[selected]
        self.root.title(f"Monitor {self.monitor_index} Preview  ({self.monitor['width']}x{self.monitor['height']})")

    def refresh_window_list(self):
        self.windows = get_open_windows()
        labels = [f"{w.title} ({w.width}x{w.height})" for w in self.windows]
        self.window_combo["values"] = labels
        if labels:
            self.window_combo.current(0)
        else:
            self.window_var.set("No windows found")

    def move_selected_window(self):
        idx = self.window_combo.current()
        if idx < 0 or idx >= len(self.windows) or self.monitor is None:
            return
        try:
            move_window_to_monitor(self.windows[idx], self.monitor)
        except Exception as e:
            print(f"Move error: {e}")

    def update_preview(self):
        try:
            if self.monitor is not None:
                shot = self.sct.grab(self.monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

                w = self.label.winfo_width()
                h = self.label.winfo_height()
                if w > 1 and h > 1:
                    img_ratio = img.width / img.height
                    box_ratio = w / h
                    if box_ratio > img_ratio:
                        new_h, new_w = h, int(h * img_ratio)
                    else:
                        new_w, new_h = w, int(w / img_ratio)
                    img = img.resize((max(1, new_w), max(1, new_h)), Image.BILINEAR)

                self.tk_img = ImageTk.PhotoImage(img)
                self.label.configure(image=self.tk_img)
        except Exception as e:
            print(f"Preview error: {e}")

        self.root.after(self.REFRESH_MS, self.update_preview)


def main():
    parser = argparse.ArgumentParser(description="Live monitor preview with window-to-monitor moving.")
    parser.add_argument("--list", action="store_true", help="List available monitors and exit")
    parser.add_argument("--monitor", type=int, default=None, help="Monitor index to preselect (see --list)")
    args = parser.parse_args()

    if args.list:
        list_monitors()
        return

    root = tk.Tk()
    ScreenPreviewApp(root, initial_monitor_index=args.monitor)
    root.mainloop()


if __name__ == "__main__":
    main()
"""
Screen Preview Tool
-------------------
Live preview window for one of your monitors, with dropdowns to pick which
monitor to preview, move any open window onto a chosen monitor (centered,
maximized or snapped to a half), and zoom the selected window.

Handy when a monitor is set to "Extend" and you can't see it directly
(e.g. a GM running a secondary display for players).

SETUP (one time):
    1. Install Python 3 from https://www.python.org/downloads/ (check "Add to PATH")
    2. pip install mss pillow pygetwindow pywin32

USAGE:
    python screen_preview.py
    python screen_preview.py --monitor 2   (preselect a monitor at launch)
    python screen_preview.py --list        (print monitor info and exit)

Window moving and zooming are Windows-only (uses pygetwindow + pywin32).
"""

import argparse
import ctypes
import os
import sys
import time
import webbrowser

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
    import win32api
    import win32con
    HAVE_PYGETWINDOW = True
except ImportError:
    HAVE_PYGETWINDOW = False

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


APP_NAME = "Screen Preview"
APP_VERSION = "dev"   # stamped by CI on release tags
REPO_URL = "https://github.com/Ookean/screen-previewer"
PRIVACY_URL = f"{REPO_URL}/blob/main/PRIVACY.md"

LAYOUTS = ["Center", "Maximize", "Left half", "Right half", "Top half", "Bottom half"]
ZOOM_KEYS = {"in": 0xBB, "out": 0xBD, "reset": 0x30}  # VK_OEM_PLUS, VK_OEM_MINUS, '0'


def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def add_text_tab(tabs, title, filename, missing_msg):
    frame = tk.Frame(tabs)
    tabs.add(frame, text=title)
    box = ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 9))
    box.pack(fill=tk.BOTH, expand=True)
    try:
        with open(resource_path(filename), encoding="utf-8") as f:
            box.insert("1.0", f.read())
    except OSError:
        box.insert("1.0", missing_msg)
    box.configure(state="disabled")


def show_about(parent):
    win = tk.Toplevel(parent)
    win.title(f"About {APP_NAME}")
    win.geometry("640x460")
    win.transient(parent)

    tabs = ttk.Notebook(win)
    tabs.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    about = tk.Frame(tabs)
    tabs.add(about, text="About")
    tk.Label(about, text=APP_NAME, font=("Segoe UI", 16, "bold")).pack(pady=(24, 2))
    tk.Label(about, text=f"Version {APP_VERSION}").pack()
    tk.Label(about, text="Live monitor preview, window mover and zoom.").pack(pady=12)
    tk.Button(about, text="Report an issue",
              command=lambda: webbrowser.open(f"{REPO_URL}/issues")).pack(pady=2)
    tk.Button(about, text="Privacy policy (online)",
              command=lambda: webbrowser.open(PRIVACY_URL)).pack(pady=2)

    add_text_tab(tabs, "Privacy", "PRIVACY.md",
                 "PRIVACY.md not found in this build.")
    add_text_tab(tabs, "Third-party licenses", "THIRD_PARTY_LICENSES.txt",
                 "License file not found. Run tools/gen_licenses.py to generate it.")


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


def move_window_to_monitor(window, monitor, layout="Center"):
    """Move a window onto a monitor and arrange it according to `layout`."""
    if window.isMinimized or window.isMaximized:
        window.restore()

    left, top, width, height = monitor["left"], monitor["top"], monitor["width"], monitor["height"]
    halves = {
        "Left half":   (left,             top,              width // 2,         height),
        "Right half":  (left + width // 2, top,             width - width // 2, height),
        "Top half":    (left,             top,              width,              height // 2),
        "Bottom half": (left,             top + height // 2, width,             height - height // 2),
    }

    if layout in halves:
        x, y, w, h = halves[layout]
        window.moveTo(x, y)
        window.resizeTo(w, h)
        window.moveTo(x, y)  # second move corrects drift between monitors with different DPI
        return

    x = left + max(0, (width - window.width) // 2)
    y = top + max(0, (height - window.height) // 2)
    window.moveTo(x, y)
    if layout == "Maximize":
        window.maximize()  # after the move, so it maximizes on the target monitor


def zoom_window(window, action):
    """Send Ctrl+Plus / Ctrl+Minus / Ctrl+0 to the window (browsers, viewers, Office...)."""
    if window.isMinimized:
        window.restore()
    try:
        window.activate()
    except Exception:
        pass  # pygetwindow can raise a spurious error even when activation worked
    time.sleep(0.15)

    key = ZOOM_KEYS[action]
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(key, 0, 0, 0)
    win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)


class ScreenPreviewApp:
    REFRESH_MS = 100  # ~10 fps

    def __init__(self, root, initial_monitor_index=None):
        self.root = root
        self.sct = mss.mss()
        self.tk_img = None

        menubar = tk.Menu(root)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About / Licenses", command=lambda: show_about(root))
        helpmenu.add_command(label="Report an issue",
                             command=lambda: webbrowser.open(f"{REPO_URL}/issues"))
        menubar.add_cascade(label="Help", menu=helpmenu)
        root.config(menu=menubar)

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
        window_row.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 3))

        tk.Label(window_row, text="Window:").pack(side=tk.LEFT, padx=(0, 6))
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(window_row, textvariable=self.window_var, state="readonly", width=40)
        self.window_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(window_row, text="Refresh", command=self.refresh_window_list).pack(side=tk.LEFT, padx=(6, 0))
        self.move_btn = tk.Button(window_row, text="Move to Monitor", command=self.move_selected_window)
        self.move_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Layout / zoom row
        layout_row = tk.Frame(root)
        layout_row.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 6))

        tk.Label(layout_row, text="Layout:").pack(side=tk.LEFT, padx=(0, 6))
        self.layout_var = tk.StringVar(value=LAYOUTS[0])
        self.layout_combo = ttk.Combobox(layout_row, textvariable=self.layout_var,
                                         values=LAYOUTS, state="readonly", width=14)
        self.layout_combo.pack(side=tk.LEFT)
        self.apply_btn = tk.Button(layout_row, text="Apply layout", command=self.apply_layout_to_window)
        self.apply_btn.pack(side=tk.LEFT, padx=(6, 0))

        tk.Label(layout_row, text="Zoom:").pack(side=tk.LEFT, padx=(16, 6))
        self.zoom_btns = [
            tk.Button(layout_row, text=text, width=4, command=lambda a=action: self.zoom_selected_window(a))
            for text, action in (("−", "out"), ("+", "in"), ("100%", "reset"))
        ]
        for btn in self.zoom_btns:
            btn.pack(side=tk.LEFT, padx=(0, 4))

        if not HAVE_PYGETWINDOW:
            self.window_combo.configure(state="disabled")
            self.layout_combo.configure(state="disabled")
            self.move_btn.configure(state="disabled")
            self.apply_btn.configure(state="disabled")
            for btn in self.zoom_btns:
                btn.configure(state="disabled")
            self.window_var.set("pygetwindow/pywin32 not installed (pip install pygetwindow pywin32)")

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

    def selected_window(self):
        idx = self.window_combo.current()
        if 0 <= idx < len(self.windows):
            return self.windows[idx]
        return None

    def move_selected_window(self):
        """Move the window to the selected monitor, centered, keeping its size."""
        self._arrange_selected_window("Center")

    def apply_layout_to_window(self):
        """Arrange the window on the selected monitor using the chosen layout."""
        self._arrange_selected_window(self.layout_var.get())

    def _arrange_selected_window(self, layout):
        window = self.selected_window()
        if window is None or self.monitor is None:
            return
        try:
            move_window_to_monitor(window, self.monitor, layout)
        except Exception as e:
            print(f"Move error: {e}")

    def zoom_selected_window(self, action):
        window = self.selected_window()
        if window is None:
            return
        try:
            zoom_window(window, action)
        except Exception as e:
            print(f"Zoom error: {e}")

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

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # keep window coordinates in real pixels
    except Exception:
        pass

    if args.list:
        list_monitors()
        return

    root = tk.Tk()
    ScreenPreviewApp(root, initial_monitor_index=args.monitor)
    root.mainloop()


if __name__ == "__main__":
    main()
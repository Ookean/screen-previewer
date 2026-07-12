"""
Screen Preview Tool
-------------------
Shows a resizable live preview window of one of your monitors, with an
in-app dropdown to pick which monitor to preview (no command line needed).

Handy when a monitor is set to "Extend" and you can't see what's on it directly
(e.g. a GM running a secondary display for players).

SETUP (one time):
    1. Install Python 3 from https://www.python.org/downloads/ (check "Add to PATH" during install)
    2. Open a terminal / command prompt and run:
         pip install mss pillow

USAGE:
    python screen_preview.py

    A dropdown at the top lets you choose which monitor to preview and
    switch between them at any time. Resize the window freely - the preview
    scales to fit while keeping the correct aspect ratio.

    Optional: you can still pre-select a monitor at launch with --monitor N,
    e.g.  python screen_preview.py --monitor 2
    (use --list to print monitor info to the terminal without opening a window)

    Close the window or press Ctrl+C in the terminal to quit.
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


class ScreenPreviewApp:
    REFRESH_MS = 100  # ~10 fps, plenty for a preview window and easy on CPU

    def __init__(self, root, initial_monitor_index=None):
        self.root = root
        self.sct = mss.mss()
        self.tk_img = None  # keep a reference so it isn't garbage collected

        self.root.title("Monitor Preview")
        self.root.geometry("900x560")
        self.root.minsize(280, 200)

        # --- Top control bar: monitor selector + refresh button ---
        controls = tk.Frame(root)
        controls.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        tk.Label(controls, text="Monitor:").pack(side=tk.LEFT, padx=(0, 6))

        self.monitor_var = tk.StringVar()
        self.combo = ttk.Combobox(controls, textvariable=self.monitor_var, state="readonly", width=40)
        self.combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo.bind("<<ComboboxSelected>>", self.on_monitor_selected)

        refresh_btn = tk.Button(controls, text="Refresh list", command=self.refresh_monitor_list)
        refresh_btn.pack(side=tk.LEFT, padx=(6, 0))

        # --- Preview area ---
        self.label = tk.Label(root, bg="black")
        self.label.pack(fill=tk.BOTH, expand=True)

        self.monitors = []       # list of monitor dicts, index in this list matches mss index - 1
        self.monitor_index = None
        self.monitor = None

        self.refresh_monitor_list(preselect=initial_monitor_index)
        self.update_preview()

    def describe_monitor(self, i, m):
        return f"{i}: {m['width']}x{m['height']} at ({m['left']},{m['top']})"

    def refresh_monitor_list(self, preselect=None):
        """Re-scan available monitors and repopulate the dropdown."""
        all_monitors = self.sct.monitors  # index 0 = combined virtual screen, skip it
        self.monitors = all_monitors[1:]

        labels = [self.describe_monitor(i, m) for i, m in enumerate(self.monitors, start=1)]
        self.combo["values"] = labels

        if not labels:
            print("No monitors detected.")
            return

        # Decide which monitor should be selected after refresh
        if preselect is not None and 1 <= preselect <= len(self.monitors):
            new_index = preselect
        elif self.monitor_index is not None and 1 <= self.monitor_index <= len(self.monitors):
            new_index = self.monitor_index  # keep current selection if still valid
        else:
            new_index = 2 if len(self.monitors) > 1 else 1  # default to secondary if present

        self.monitor_index = new_index
        self.monitor = self.monitors[new_index - 1]
        self.combo.current(new_index - 1)
        self.root.title(f"Monitor {new_index} Preview  ({self.monitor['width']}x{self.monitor['height']})")

    def on_monitor_selected(self, event=None):
        selected = self.combo.current()  # 0-based index into self.monitors
        self.monitor_index = selected + 1
        self.monitor = self.monitors[selected]
        self.root.title(f"Monitor {self.monitor_index} Preview  ({self.monitor['width']}x{self.monitor['height']})")

    def update_preview(self):
        try:
            if self.monitor is not None:
                shot = self.sct.grab(self.monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

                # Fit image into current label size while keeping aspect ratio
                w = self.label.winfo_width()
                h = self.label.winfo_height()
                if w > 1 and h > 1:
                    img_ratio = img.width / img.height
                    box_ratio = w / h
                    if box_ratio > img_ratio:
                        new_h = h
                        new_w = int(h * img_ratio)
                    else:
                        new_w = w
                        new_h = int(w / img_ratio)
                    new_w = max(1, new_w)
                    new_h = max(1, new_h)
                    img = img.resize((new_w, new_h), Image.BILINEAR)

                self.tk_img = ImageTk.PhotoImage(img)
                self.label.configure(image=self.tk_img)
        except Exception as e:
            print(f"Preview error: {e}")

        self.root.after(self.REFRESH_MS, self.update_preview)


def main():
    parser = argparse.ArgumentParser(description="Live preview window for a monitor, with in-app monitor selection.")
    parser.add_argument("--list", action="store_true", help="List available monitors in the terminal and exit")
    parser.add_argument("--monitor", type=int, default=None, help="Monitor index to preselect at launch (see --list)")
    args = parser.parse_args()

    if args.list:
        list_monitors()
        return

    root = tk.Tk()
    ScreenPreviewApp(root, initial_monitor_index=args.monitor)
    root.mainloop()


if __name__ == "__main__":
    main()
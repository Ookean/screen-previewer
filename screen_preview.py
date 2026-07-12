"""
Screen Preview Tool
-------------------
Shows a resizable live preview window of one of your monitors.
Handy when a monitor is set to "Extend" and you can't see what's on it directly
(e.g. a GM running a secondary display for players).

SETUP (one time):
    1. Install Python 3 from https://www.python.org/downloads/ (check "Add to PATH" during install)
    2. Open a terminal / command prompt and run:
         pip install mss pillow

USAGE:
    List available monitors (to find out which index is your secondary monitor):
         python screen_preview.py --list

    Show a live preview of monitor 2 (adjust the number based on --list output):
         python screen_preview.py --monitor 2

    If you don't pass --monitor, it defaults to monitor 2 (your typical "secondary" screen),
    falling back to monitor 1 if there's no second monitor.

    Resize the window freely - the preview scales to fit while keeping the correct aspect ratio.
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

    def __init__(self, root, monitor_index):
        self.root = root
        self.sct = mss.mss()
        monitors = self.sct.monitors

        if monitor_index < 1 or monitor_index >= len(monitors):
            print(f"Monitor index {monitor_index} not available. Falling back to monitor 1.")
            monitor_index = 1

        self.monitor_index = monitor_index
        self.monitor = monitors[monitor_index]

        self.root.title(f"Monitor {monitor_index} Preview  ({self.monitor['width']}x{self.monitor['height']})")
        self.root.geometry("900x520")
        self.root.minsize(240, 160)

        self.label = tk.Label(root, bg="black")
        self.label.pack(fill=tk.BOTH, expand=True)

        self.tk_img = None  # keep a reference so it isn't garbage collected
        self.update_preview()

    def update_preview(self):
        try:
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
    parser = argparse.ArgumentParser(description="Live preview window for a monitor.")
    parser.add_argument("--list", action="store_true", help="List available monitors and exit")
    parser.add_argument("--monitor", type=int, default=None, help="Monitor index to preview (see --list)")
    args = parser.parse_args()

    if args.list:
        list_monitors()
        return

    monitor_index = args.monitor
    if monitor_index is None:
        with mss.mss() as sct:
            monitor_index = 2 if len(sct.monitors) > 2 else 1

    root = tk.Tk()
    ScreenPreviewApp(root, monitor_index)
    root.mainloop()


if __name__ == "__main__":
    main()
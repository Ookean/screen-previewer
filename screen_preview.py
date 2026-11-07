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
    2. pip install -r requirements.txt

USAGE:
    python screen_preview.py

Window moving, layouts and zoom are Windows-only (pygetwindow + pywin32).

LAYOUT OF THE CODE (package `previewer`):
    app.py              main window: assembles the pieces below
    menubar.py          menu bar            about.py   About / privacy / licenses window
    monitors.py         monitor list and selection
    window_control.py   list windows, layouts, zoom (the Windows-specific part)
    panels/             one widget per feature: monitor, window, layout, zoom, preview
"""
import tkinter as tk

from previewer import window_control
from previewer.app import ScreenPreviewApp


def main():
    window_control.enable_dpi_awareness()   # must run before the first window is created
    root = tk.Tk()
    ScreenPreviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .config import APP_NAME, APP_VERSION, PRIVACY_URL, REPO_URL, resource_path


def open_issues():
    webbrowser.open(f"{REPO_URL}/issues")


def add_text_tab(tabs, title, filename, missing_msg):
    frame = tk.Frame(tabs)
    tabs.add(frame, text=title)
    box = ScrolledText(frame, wrap=tk.WORD, font="TkFixedFont")
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

    # Keep a reference: a tkinter Font object deletes its Tk font when garbage collected.
    win.title_font = tkfont.nametofont("TkDefaultFont").copy()
    win.title_font.configure(size=16, weight="bold")

    tabs = ttk.Notebook(win)
    tabs.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    about = tk.Frame(tabs)
    tabs.add(about, text="About")
    tk.Label(about, text=APP_NAME, font=win.title_font).pack(pady=(24, 2))
    tk.Label(about, text=f"Version {APP_VERSION}").pack()
    tk.Label(about, text="Live monitor preview, window mover and zoom.").pack(pady=12)
    tk.Button(about, text="Report an issue", command=open_issues).pack(pady=2)
    tk.Button(about, text="Privacy policy (online)",
              command=lambda: webbrowser.open(PRIVACY_URL)).pack(pady=2)

    add_text_tab(tabs, "Privacy", "PRIVACY.md",
                 "PRIVACY.md not found in this build.")
    add_text_tab(tabs, "Third-party licenses", "THIRD_PARTY_LICENSES.txt",
                 "License file not found. Run tools/gen_licenses.py to generate it.")
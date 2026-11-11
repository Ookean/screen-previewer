"""About window with the privacy policy and third-party license texts."""
import os
import tkinter as tk
import urllib.parse
import webbrowser
from tkinter import font as tkfont
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from . import i18n
from .config import APP_NAME, APP_VERSION, PRIVACY_URL, REPO_URL, desktop_info, resource_path
from .i18n import t


def open_issues():
    webbrowser.open(f"{REPO_URL}/issues")


def open_desktop_issue():
    """Open a new GitHub issue in the browser, with the user's desktop already filled in for them to review."""
    body = (f"My desktop is not fully supported yet.\n\nDesktop / session / distribution: {desktop_info()}\n"
            f"Screen Preview version: {APP_VERSION}\n\nWhat I expected to work:\n")
    query = urllib.parse.urlencode({"title": "Support for my desktop", "body": body})
    webbrowser.open(f"{REPO_URL}/issues/new?{query}")


def privacy_path():
    """The privacy policy in the current language, or the English PRIVACY.md if there is no translation.

    A translation is a file previewer/locales/privacy.<code>.md, e.g. privacy.de.md.
    """
    translated = resource_path(f"previewer/locales/privacy.{i18n.current_language()}.md")
    return translated if os.path.exists(translated) else resource_path("PRIVACY.md")


def add_text_tab(tabs, title, path, missing_msg):
    frame = tk.Frame(tabs)
    tabs.add(frame, text=title)
    box = ScrolledText(frame, wrap=tk.WORD, font="TkFixedFont")
    box.pack(fill=tk.BOTH, expand=True)
    try:
        with open(path, encoding="utf-8") as f:
            box.insert("1.0", f.read())
    except OSError:
        box.insert("1.0", missing_msg)
    box.configure(state="disabled")


def show_about(parent):
    win = tk.Toplevel(parent)
    win.title(t("about.title", app=APP_NAME))
    win.geometry("640x460")
    win.transient(parent)

    # Keep a reference: a tkinter Font object deletes its Tk font when garbage collected.
    win.title_font = tkfont.nametofont("TkDefaultFont").copy()
    win.title_font.configure(size=16, weight="bold")

    tabs = ttk.Notebook(win)
    tabs.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    about = tk.Frame(tabs)
    tabs.add(about, text=t("about.tab_about"))
    tk.Label(about, text=APP_NAME, font=win.title_font).pack(pady=(24, 2))
    tk.Label(about, text=t("about.version", version=APP_VERSION)).pack()
    tk.Label(about, text=t("about.description")).pack(pady=12)
    tk.Button(about, text=t("about.report_issue"), command=open_issues).pack(pady=2)
    tk.Button(about, text=t("about.privacy_online"),
              command=lambda: webbrowser.open(PRIVACY_URL)).pack(pady=2)

    add_text_tab(tabs, t("about.tab_privacy"), privacy_path(), t("about.privacy_missing"))
    add_text_tab(tabs, t("about.tab_licenses"), resource_path("THIRD_PARTY_LICENSES.txt"),
                 t("about.licenses_missing"))

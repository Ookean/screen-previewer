import tkinter as tk

from .about import open_issues, show_about


def build_menubar(root):
    menubar = tk.Menu(root)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About / Licenses", command=lambda: show_about(root))
    helpmenu.add_command(label="Report an issue", command=open_issues)
    menubar.add_cascade(label="Help", menu=helpmenu)
    root.config(menu=menubar)
    return menubar
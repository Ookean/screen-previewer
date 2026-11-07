"""The window's menu bar: Settings (language) and Help."""
import tkinter as tk

from . import i18n
from .about import open_issues, show_about
from .i18n import t


def build_menubar(root, settings, on_language_change):
    """Create the menu bar, attach it to `root` and return it.

    `on_language_change(preference)` is called with "system" or a language code
    when the user picks a language.
    """
    menubar = tk.Menu(root)

    settings_menu = tk.Menu(menubar, tearoff=0)
    language_menu = tk.Menu(settings_menu, tearoff=0)
    menubar.language_var = tk.StringVar(value=settings.language)   # keep a reference to the variable
    choices = [(i18n.SYSTEM, t("menu.language_system"))] + i18n.available_languages()
    for code, name in choices:
        language_menu.add_radiobutton(label=name, value=code, variable=menubar.language_var,
                                      command=lambda c=code: on_language_change(c))
    settings_menu.add_cascade(label=t("menu.language"), menu=language_menu)
    menubar.add_cascade(label=t("menu.settings"), menu=settings_menu)

    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label=t("menu.about"), command=lambda: show_about(root))
    help_menu.add_command(label=t("menu.report_issue"), command=open_issues)
    menubar.add_cascade(label=t("menu.help"), menu=help_menu)

    root.config(menu=menubar)
    return menubar

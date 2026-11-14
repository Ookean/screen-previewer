"""The window's menu bar: Settings (language, appearance) and Help."""
from PySide6.QtGui import QActionGroup

from . import i18n
from .about import open_issues, show_about
from .i18n import t
from .settings import THEME_CHOICES


def _choice_menu(parent_menu, title, choices, selected, on_choose):
    """A submenu with one checkable entry per (value, label) in `choices`; picking one calls on_choose(value)."""
    menu = parent_menu.addMenu(title)
    group = QActionGroup(menu)          # makes the entries behave like radio buttons
    group.setExclusive(True)
    for value, label in choices:
        action = menu.addAction(label)
        action.setCheckable(True)
        action.setChecked(value == selected)
        group.addAction(action)
        action.triggered.connect(lambda checked=False, v=value: on_choose(v))
    return menu


def build_menus(window, settings, on_language_change, on_theme_change):
    """Fill the window's menu bar.

    `on_language_change(preference)` gets "system" or a language code, `on_theme_change(preference)` gets
    "system", "light" or "dark".
    """
    bar = window.menuBar()
    bar.clear()

    settings_menu = bar.addMenu(t("menu.settings"))
    languages = [(i18n.SYSTEM, t("menu.language_system"))] + i18n.available_languages()
    _choice_menu(settings_menu, t("menu.language"), languages, settings.language, on_language_change)
    themes = [(name, t(f"menu.theme_{name}")) for name in THEME_CHOICES]
    _choice_menu(settings_menu, t("menu.theme"), themes, settings.theme, on_theme_change)

    help_menu = bar.addMenu(t("menu.help"))
    help_menu.addAction(t("menu.about")).triggered.connect(lambda *_: show_about(window))
    help_menu.addAction(t("menu.report_issue")).triggered.connect(lambda *_: open_issues())

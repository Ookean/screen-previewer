"""
Screen Preview Tool
-------------------
Live preview window for one of your monitors, with controls to pick which monitor to preview, move any
open window onto a chosen monitor (centered, maximized or snapped to a half), and zoom the selected window.

Handy when a monitor is set to "Extend" and you can't see it directly
(e.g. a GM running a secondary display for players).

SETUP (one time):
    1. Install Python 3 from https://www.python.org/downloads/ (check "Add to PATH")
    2. pip install -r requirements.txt

USAGE:
    python screen_preview.py

LAYOUT OF THE CODE (package `previewer`):
    app.py              main window: sidebar of control cards next to the preview; rebuilds on a language/theme change
    theme.py, icons.py  light and dark look, layout button pictures
    widgets.py          shared building blocks (cards, drop-downs)
    menubar.py          Settings (language, appearance) and Help menus
    about.py            About / privacy / licenses window
    i18n.py, locales/   translations: one JSON file per language
    settings.py         saved preferences (language, appearance)
    monitors.py         monitor list and selection
    capture.py, portal.py   where the preview's pixels come from (screen grab, or the Wayland portal)
    window_control.py   list windows, layouts, zoom: Windows (_win32.py), Linux X11 (_x11.py), Wayland (wayland/)
    panels/             monitor picker, window controls, live preview
"""
import sys

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from previewer import i18n, theme
from previewer.app import ScreenPreviewApp
from previewer.config import resource_path
from previewer.settings import Settings


def main():
    app = QApplication(sys.argv)
    QGuiApplication.setDesktopFileName("screen-preview")   # lets Linux desktops match the window to its launcher icon
    app.setWindowIcon(QIcon(resource_path("Assets/icon.ico")))

    settings = Settings()
    i18n.set_language(settings.language)
    theme.apply(app, settings.theme)

    window = ScreenPreviewApp(settings)
    window.follow_system_theme()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

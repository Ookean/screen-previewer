"""The look of the app: light and dark colour schemes, and one style sheet built from them.

`apply(app, preference)` takes "system", "light" or "dark". With "system" the app follows the operating
system's setting, also while it is running.
"""
import sys
from string import Template

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette

SYSTEM = "system"

LIGHT = dict(bg="#F3F4F7", card="#FFFFFF", card_alt="#ECEEF3", hover="#E1E4EC", text="#1B1F29", muted="#6A7283",
             border="#DCDFE7", accent="#4F6BED", accent_hover="#415CDB", accent_text="#FFFFFF",
             accent_soft="#E3E8FD", preview="#0B0C10")
DARK = dict(bg="#14161B", card="#1D2027", card_alt="#262A33", hover="#303541", text="#E7E9EF", muted="#9AA1B0",
            border="#2C303B", accent="#7B8CFF", accent_hover="#92A0FF", accent_text="#10131A",
            accent_soft="#2B3252", preview="#000000")

_STYLE = Template("""
QMainWindow, QDialog { background: $bg; }
QWidget { color: $text; font-size: 10pt; }
QScrollArea, QWidget#sidebar { background: transparent; border: none; }
QFrame#card { background: $card; border: 1px solid $border; border-radius: 12px; }
QLabel { background: transparent; }
QLabel#sectionTitle { color: $muted; font-size: 8pt; font-weight: 600; }
QLabel#muted { color: $muted; }
QLabel#hint { color: $muted; font-size: 9pt; }
QLabel#preview { background: $preview; color: #C9CEDA; border-radius: 12px; }
QPushButton { background: $card_alt; border: 1px solid $border; border-radius: 8px; padding: 7px 14px; min-height: 18px; }
QPushButton:hover { background: $hover; }
QPushButton:pressed { background: $border; }
QPushButton:disabled { color: $muted; background: $bg; }
QPushButton#primary { background: $accent; color: $accent_text; border: none; font-weight: 600; }
QPushButton#primary:hover { background: $accent_hover; }
QPushButton#primary:disabled { background: $card_alt; color: $muted; }
QToolButton#layoutTile { background: $card_alt; border: 1px solid $border; border-radius: 8px; padding: 4px; }
QToolButton#layoutTile:hover { background: $hover; }
QToolButton#layoutTile:checked { background: $accent_soft; border: 2px solid $accent; }
QToolButton#layoutTile:disabled { background: $bg; }
QComboBox { background: $card_alt; border: 1px solid $border; border-radius: 8px; padding: 6px 10px; min-height: 18px; }
QComboBox:hover { border-color: $accent; }
QComboBox:disabled { color: $muted; background: $bg; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: $card; border: 1px solid $border; border-radius: 8px;
    selection-background-color: $accent; selection-color: $accent_text; outline: 0; padding: 4px; }
QMenuBar { background: $bg; }
QMenuBar::item { padding: 6px 12px; border-radius: 6px; background: transparent; }
QMenuBar::item:selected { background: $hover; }
QMenu { background: $card; border: 1px solid $border; border-radius: 8px; padding: 6px; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: $accent; color: $accent_text; }
QStatusBar { background: $bg; color: $muted; }
QStatusBar::item { border: none; }
QTabWidget::pane { border: 1px solid $border; border-radius: 8px; background: $card; top: -1px; }
QTabBar::tab { background: transparent; padding: 8px 16px; color: $muted; border: none; }
QTabBar::tab:selected { color: $text; border-bottom: 2px solid $accent; }
QPlainTextEdit { background: $card; border: none; font-family: monospace; }
QToolTip { background: $card; color: $text; border: 1px solid $border; padding: 4px; }
QScrollBar:vertical { width: 10px; background: transparent; margin: 0; }
QScrollBar::handle:vertical { background: $border; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""")

_current = LIGHT
_system_looks_dark = None   # remembered from the platform palette before we replace it


def colors():
    """The colour scheme that is in use now."""
    return _current


def _font():
    font = QFont()
    families = (["Segoe UI Variable Text", "Segoe UI"] if sys.platform == "win32"
                else ["Inter", "Noto Sans", "Cantarell", "Ubuntu", "DejaVu Sans"])
    font.setFamilies(families)    # the first one that is installed is used
    font.setPointSize(10)
    return font


def _system_is_dark(app):
    hints = app.styleHints()
    try:
        hints.setColorScheme(Qt.ColorScheme.Unknown)     # drop an earlier forced scheme: follow the system
        return hints.colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:                               # Qt older than 6.8
        global _system_looks_dark
        if _system_looks_dark is None:
            _system_looks_dark = app.palette().window().color().lightness() < 128
        return _system_looks_dark


def _palette(c):
    palette = QPalette()
    for role, key in ((QPalette.ColorRole.Window, "bg"), (QPalette.ColorRole.WindowText, "text"),
                      (QPalette.ColorRole.Base, "card"), (QPalette.ColorRole.AlternateBase, "card_alt"),
                      (QPalette.ColorRole.Text, "text"), (QPalette.ColorRole.Button, "card_alt"),
                      (QPalette.ColorRole.ButtonText, "text"), (QPalette.ColorRole.Highlight, "accent"),
                      (QPalette.ColorRole.HighlightedText, "accent_text"), (QPalette.ColorRole.ToolTipBase, "card"),
                      (QPalette.ColorRole.ToolTipText, "text"), (QPalette.ColorRole.PlaceholderText, "muted"),
                      (QPalette.ColorRole.Link, "accent")):
        palette.setColor(role, QColor(c[key]))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(c["muted"]))
    return palette


def apply(app, preference=SYSTEM):
    """Paint the whole app in the chosen scheme."""
    global _current
    dark = _system_is_dark(app) if preference == SYSTEM else preference == "dark"
    if preference != SYSTEM:
        try:
            app.styleHints().setColorScheme(Qt.ColorScheme.Dark if dark else Qt.ColorScheme.Light)   # dark title bar too
        except AttributeError:
            pass
    _current = DARK if dark else LIGHT
    app.setStyle("Fusion")                  # the same base look on every platform; the style sheet does the rest
    app.setFont(_font())
    app.setPalette(_palette(_current))
    app.setStyleSheet(_STYLE.substitute(_current))

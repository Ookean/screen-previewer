"""About window with the privacy policy and third-party license texts."""
import os
import urllib.parse
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget

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


def _text_tab(path, missing_msg):
    box = QPlainTextEdit()
    box.setReadOnly(True)
    try:
        with open(path, encoding="utf-8") as f:
            box.setPlainText(f.read())
    except OSError:
        box.setPlainText(missing_msg)
    return box


def show_about(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle(t("about.title", app=APP_NAME))
    dialog.resize(660, 500)
    layout = QVBoxLayout(dialog)
    tabs = QTabWidget()
    layout.addWidget(tabs)

    page = QWidget()
    column = QVBoxLayout(page)
    column.setAlignment(Qt.AlignmentFlag.AlignCenter)
    column.setSpacing(10)
    title = QLabel(APP_NAME)
    title.setStyleSheet("font-size: 20pt; font-weight: 700;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    column.addWidget(title)
    for text, muted in ((t("about.version", version=APP_VERSION), True), (t("about.description"), False)):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        if muted:
            label.setObjectName("muted")
        column.addWidget(label)
    for text, action in ((t("about.report_issue"), open_issues),
                         (t("about.privacy_online"), lambda: webbrowser.open(PRIVACY_URL))):
        button = QPushButton(text)
        button.clicked.connect(lambda checked=False, run=action: run())
        column.addWidget(button)
    tabs.addTab(page, t("about.tab_about"))
    tabs.addTab(_text_tab(privacy_path(), t("about.privacy_missing")), t("about.tab_privacy"))
    tabs.addTab(_text_tab(resource_path("THIRD_PARTY_LICENSES.txt"), t("about.licenses_missing")), t("about.tab_licenses"))
    dialog.exec()

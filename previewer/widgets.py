"""Small building blocks shared by the panels."""
from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout


class Card(QFrame):
    """A rounded box with an optional small upper-case title. Put content into `self.body`."""

    def __init__(self, title=None):
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(14, 12, 14, 14)
        self.body.setSpacing(8)
        if title:
            label = QLabel(title.upper())
            label.setObjectName("sectionTitle")
            self.body.addWidget(label)


class PopupComboBox(QComboBox):
    """A drop-down that reloads its entries each time it is opened, so lists never look stale."""

    def __init__(self, on_popup=None):
        super().__init__()
        self.on_popup = on_popup
        # Long window titles must not make the sidebar wider.
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(16)

    def showPopup(self):
        if self.on_popup is not None:
            self.on_popup()
        super().showPopup()

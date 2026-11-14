"""Feature: the live preview of the selected monitor."""
from PIL import Image
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from ..i18n import t


class PreviewPanel(QLabel):
    REFRESH_MS = 100  # ~10 fps

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setObjectName("preview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumSize(1, 1)
        # Ignore the picture's size, or a big frame would stop the window from shrinking.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)

    def start(self):
        self._update()
        self._timer.start(self.REFRESH_MS)

    def _update(self):
        try:
            monitor = self.model.current
            img = None if monitor is None else self.model.capture.grab(monitor)
            if img is not None:
                self.setPixmap(self._to_pixmap(img))
            else:
                status = self.model.capture.status()   # e.g. Wayland: waiting for the permission dialog
                if status:
                    self.clear()
                    self.setText(t(status[0], **status[1]))
        except Exception as e:
            print(f"Preview error: {e}")

    def _to_pixmap(self, img):
        """Scale the frame to fit this label (keeping its shape) and turn it into a pixmap."""
        ratio = self.devicePixelRatioF()
        w, h = int(self.width() * ratio), int(self.height() * ratio)
        if w > 1 and h > 1:
            scale = min(w / img.width, h / img.height)
            img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
        img = img.convert("RGB")
        picture = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(picture)     # copies the pixels, so the bytes above may go away
        pixmap.setDevicePixelRatio(ratio)
        return pixmap

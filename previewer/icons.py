"""Small pictures for the layout buttons: a screen with the window's place highlighted."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

# Where the window sits on the screen for each layout id: (x, y, width, height) as fractions of the screen.
_REGIONS = {
    "center": (0.25, 0.2, 0.5, 0.6),
    "maximize": (0.0, 0.0, 1.0, 1.0),
    "left_half": (0.0, 0.0, 0.5, 1.0),
    "right_half": (0.5, 0.0, 0.5, 1.0),
    "top_half": (0.0, 0.0, 1.0, 0.5),
    "bottom_half": (0.0, 0.5, 1.0, 0.5),
}


def layout_icon(layout_id, color, size=34):
    """An icon `size` pixels wide for the layout `layout_id`, drawn in `color` (a '#rrggbb' string)."""
    scale = 2                                   # draw at double size so it stays sharp on sharp screens
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    screen = QRectF(2.5, size * 0.2, size - 5, (size - 5) * 0.62)
    x, y, w, h = _REGIONS[layout_id]
    window = QRectF(screen.x() + x * screen.width(), screen.y() + y * screen.height(),
                    w * screen.width(), h * screen.height()).adjusted(2, 2, -2, -2)
    fill = QColor(color)
    fill.setAlpha(150)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(fill)
    painter.drawRoundedRect(window, 2, 2)
    painter.setPen(QPen(QColor(color), 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(screen, 3, 3)
    painter.end()
    return QIcon(pixmap)

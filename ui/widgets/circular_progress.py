from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient
from ui.themes.theme_manager import ThemeManager


class CircularProgress(QWidget):
    """
    A premium circular progress indicator for displaying confidence scores.

    Tiers:
      - 95–100  →  Excellent  (green)
      - 80–94   →  Great      (yellow/amber)
      - <80     →  Poor       (red)
    """

    def __init__(self, score: int = 0, size: int = 64, parent=None):
        super().__init__(parent)
        self._score = max(0, min(100, score))
        self._size = size
        self.setFixedSize(size, size + 22)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, value: int):
        self._score = max(0, min(100, value))
        self.update()

    def _tier(self):
        if self._score >= 95:
            return "Excellent", QColor(ThemeManager.get_color("success"))
        elif self._score >= 80:
            return "Great", QColor(ThemeManager.get_color("warning"))
        else:
            return "Poor", QColor(ThemeManager.get_color("danger"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        label, color = self._tier()

        # Circle geometry
        pen_width = 5
        margin = pen_width / 2 + 2
        diameter = self._size - pen_width - 4
        rect = QRectF(margin, margin, diameter, diameter)

        # Track (background arc)
        track_pen = QPen(QColor(255, 255, 255, 18), pen_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Progress arc
        progress_pen = QPen(color, pen_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(progress_pen)
        span = int(self._score / 100.0 * 360 * 16)
        # Start from 12 o'clock position (90 degrees in Qt coordinates)
        painter.drawArc(rect, 90 * 16, -span)

        # Score text inside circle
        text_color = QColor(ThemeManager.get_color("text_primary"))
        painter.setPen(text_color)
        font = QFont()
        font.setPixelSize(int(self._size * 0.26))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{self._score}%")

        # Label text below circle
        painter.setPen(QPen(color))
        label_font = QFont()
        label_font.setPixelSize(9)
        label_font.setBold(True)
        painter.setFont(label_font)
        label_rect = QRectF(0, self._size - 2, self._size, 20)
        painter.drawText(label_rect, Qt.AlignHCenter | Qt.AlignTop, label)

        painter.end()

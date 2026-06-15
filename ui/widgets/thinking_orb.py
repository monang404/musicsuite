from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor, QPainterPath
from ui.themes.theme_manager import ThemeManager

class ThinkingOrb(QWidget):
    """
    Animated pulsating orb with 3 dots that bounce sequentially.
    Similar to Claude's thinking indicator.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 24)
        
        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        
    def start(self):
        self._step = 0
        self._timer.start(150)
        self.show()
        
    def stop(self):
        self._timer.stop()
        self.hide()
        
    def _tick(self):
        self._step += 1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        accent = QColor(ThemeManager.get_color('accent'))
        
        # Draw 3 dots
        dot_radius = 4
        spacing = 14
        start_x = (self.width() - (2 * spacing)) / 2
        center_y = self.height() / 2
        
        for i in range(3):
            # Calculate bounce offset
            offset = 0
            if (self._step % 6) == i:
                offset = -4
            elif (self._step % 6) == (i + 1) % 6:
                offset = -2
                
            x = start_x + (i * spacing)
            y = center_y + offset
            
            # Draw dot
            painter.setBrush(accent)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2))

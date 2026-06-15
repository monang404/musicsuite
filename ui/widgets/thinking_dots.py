from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer
from ui.themes.theme_manager import ThemeManager

class ThinkingDots(QLabel):
    """
    Menampilkan animasi "..." yang bergerak: "  " → ".  " → ".. " → "..."
    Reset dan ulang setiap 400ms.
    """
    def __init__(self, prefix="", parent=None):
        super().__init__(parent)
        self.prefix = prefix
        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-size: 13px;")
    
    def start(self):
        self._step = 0
        self._timer.start(400)
        self.show()
    
    def stop(self):
        self._timer.stop()
        self.hide()
    
    def _tick(self):
        dots = ["   ", ".  ", ".. ", "..."][self._step % 4]
        self.setText(f"{self.prefix}{dots}")
        self._step += 1

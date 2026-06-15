import os
import sys
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QFontDatabase
from PySide6.QtCore import Qt

def create_app_icon():
    os.makedirs("assets/icons", exist_ok=True)
    size = 256
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Background (#1e1d1b)
    painter.setBrush(QColor("#1e1d1b"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, size, size, 40, 40)
    
    # Accent color (#e8631a) for the music note
    painter.setPen(QColor("#e8631a"))
    font = painter.font()
    font.setPixelSize(150)
    font.setBold(True)
    painter.setFont(font)
    
    painter.drawText(image.rect(), Qt.AlignCenter, "♪")
    
    painter.end()
    
    icon_path = os.path.join("assets", "icons", "app_icon.png")
    image.save(icon_path)
    print(f"Generated {icon_path}")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    create_app_icon()

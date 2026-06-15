import os
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter
from ui.themes.theme_manager import ThemeManager

class SidebarNavButton(QPushButton):
    """
    Custom sidebar navigation button.
    38x38px, icon-only, active/inactive state, border-radius: 9px.
    Dynamically recolors SVG icons based on active/hover state.
    """
    def __init__(self, icon_path: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
            
        self._active = False
        self._hovered = False
        self.update_state()

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self.update_state()

    def enterEvent(self, event):
        self._hovered = True
        self.update_state()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update_state()
        super().leaveEvent(event)

    def _get_recolored_icon(self, color: str) -> QIcon:
        """
        Reads the SVG, replaces currentColor with the target color, and returns a QIcon.
        """
        if not os.path.exists(self.icon_path):
            return QIcon()
        painter = None
        try:
            with open(self.icon_path, "r", encoding="utf-8") as f:
                svg_data = f.read()
            # Replace currentColor with our hex color
            recolored_svg = svg_data.replace("currentColor", color)
            
            # Render SVG to QPixmap
            renderer = QSvgRenderer(recolored_svg.encode("utf-8"))
            pixmap = QPixmap(30, 30)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            # Center the 16x16 icon in 30x30 canvas
            renderer.render(painter, QRect(7, 7, 16, 16))
            return QIcon(pixmap)
        except Exception as e:
            print(f"Error loading/recoloring SVG {self.icon_path}: {e}")
            return QIcon(self.icon_path)
        finally:
            if painter is not None and painter.isActive():
                painter.end()

    def update_state(self):
        accent = ThemeManager.get_color("accent")
        accent_muted = ThemeManager.get_color("accent_muted")
        accent_border = ThemeManager.get_color("accent_border")
        text_secondary = ThemeManager.get_color("text_secondary")
        text_muted = ThemeManager.get_color("text_muted")

        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent_muted};
                    border: 1px solid {accent_border};
                    border-radius: 6px;
                    padding: 0px;
                }}
            """)
            self.setIcon(self._get_recolored_icon(accent))
        else:
            if self._hovered:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(255, 255, 255, 0.06);
                        border: 1px solid transparent;
                        border-radius: 6px;
                        padding: 0px;
                    }}
                """)
                self.setIcon(self._get_recolored_icon(text_secondary))
            else:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        border: 1px solid transparent;
                        border-radius: 6px;
                        padding: 0px;
                    }}
                """)
                self.setIcon(self._get_recolored_icon(text_muted))
        self.setIconSize(QSize(30, 30)) # Use full pixmap canvas size

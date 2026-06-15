from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from ui.themes.theme_manager import ThemeManager

class SidebarBadge(QLabel):
    """
    Sidebar badge widget to display active/queued job counts.
    16px circular badge, accent background, 9px bold white text.
    Overlays on the parent widget.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setAlignment(Qt.AlignCenter)
        self.update_style()
        self.hide()

    def update_style(self):
        accent = ThemeManager.get_color("accent")
        # 8px border-radius makes the 16x16 label a perfect circle
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {accent};
                color: #ffffff;
                font-size: 9px;
                font-weight: bold;
                border-radius: 8px;
                padding: 0px;
            }}
        """)

    def set_count(self, count: int):
        if count > 0:
            self.setText(str(count))
            self.show()
            self.adjust_position()
        else:
            self.hide()

    def adjust_position(self):
        if self.parentWidget():
            # Align to the top-right corner of the parent button
            parent_width = self.parentWidget().width()
            # Move the badge slightly top-right (overlaying the edge)
            self.move(parent_width - 14, -2)

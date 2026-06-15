import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QMouseEvent
from ui.themes.theme_manager import ThemeManager

class CustomTitleBar(QFrame):
    def __init__(self, parent: QWidget, title: str = "", show_minimize=True, show_maximize=True):
        super().__init__(parent)
        self.parent_window = parent
        self.show_minimize = show_minimize
        self.show_maximize = show_maximize
        
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_hover')};
            }}
            QPushButton#close_btn:hover {{
                background-color: #e81123;
            }}
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 4, 0)
        self.layout.setSpacing(4)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {ThemeManager.get_color('text_primary')}; font-weight: bold; font-size: 13px; background: transparent;")
        
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()
        
        self.right_layout = QHBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 10, 0)
        self.right_layout.setSpacing(8)
        self.layout.addLayout(self.right_layout)
        
        icon_path = os.path.join("assets", "icons")
        
        if self.show_minimize:
            self.min_btn = QPushButton()
            self.min_btn.setIcon(QIcon(os.path.join(icon_path, "icon_minimize.svg")))
            self.min_btn.setFixedSize(28, 28)
            self.min_btn.clicked.connect(self._on_minimize)
            self.layout.addWidget(self.min_btn)
            
        if self.show_maximize:
            self.max_btn = QPushButton()
            self.max_btn.setIcon(QIcon(os.path.join(icon_path, "icon_maximize.svg")))
            self.max_btn.setFixedSize(28, 28)
            self.max_btn.clicked.connect(self._on_maximize)
            self.layout.addWidget(self.max_btn)
            
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setIcon(QIcon(os.path.join(icon_path, "icon_close.svg")))
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self._on_close)
        self.layout.addWidget(self.close_btn)
        
        # Variables for dragging
        self._is_dragging = False
        self._drag_start_pos = QPoint()

    def _on_minimize(self):
        self.parent_window.showMinimized()

    def _on_maximize(self):
        is_max = self.parent_window.isMaximized()
        screen_geom = self.parent_window.screen().availableGeometry()
        window_geom = self.parent_window.geometry()
        
        # Deteksi jika window di-maximize paksa oleh Windows Aero Snap (tarik ke atas)
        # Windows frameless seringkali tidak register isMaximized() saat Aero Snap.
        is_visually_maximized = (
            window_geom.width() >= screen_geom.width() - 20 and
            window_geom.height() >= screen_geom.height() - 20
        )
        
        if is_max or is_visually_maximized:
            self.parent_window.showNormal()
            # Jika ini adalah Aero Snap, paksa kembalikan ke ukuran sebelum di-snap
            if not is_max and hasattr(self.parent_window, '_normal_geometry'):
                self.parent_window.setGeometry(self.parent_window._normal_geometry)
                
            self.max_btn.setIcon(QIcon(os.path.join("assets", "icons", "icon_maximize.svg")))
        else:
            self.parent_window._normal_geometry = self.parent_window.geometry()
            self.parent_window.showMaximized()
            self.max_btn.setIcon(QIcon(os.path.join("assets", "icons", "icon_restore.svg")))

    def _on_close(self):
        self.parent_window.close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            
            # Simpan ukuran normal sebelum window ditarik (untuk antisipasi Aero Snap)
            if not self.parent_window.isMaximized():
                self.parent_window._normal_geometry = self.parent_window.geometry()
                
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._is_dragging = False
        event.accept()
        
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.show_maximize and event.button() == Qt.LeftButton:
            self._on_maximize()
            event.accept()

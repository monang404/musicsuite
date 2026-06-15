import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QFileDialog, QWidget
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from ui.themes.theme_manager import ThemeManager
from ui.core.app_settings import AppSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(520)
        
        bg_card = ThemeManager.get_color('bg_card')
        text_primary = ThemeManager.get_color('text_primary')
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_card};
                border: 1px solid {ThemeManager.get_color('border')};
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        
        # Add fade-in animation
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(300)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._fade_anim_slot = None
        self._fade_anim.start()
        
        self._build_ui()
        
    def _build_ui(self):
        text_primary = ThemeManager.get_color('text_primary')
        text_secondary = ThemeManager.get_color('text_secondary')
        bg_main = ThemeManager.get_color('bg_main')
        accent = ThemeManager.get_color('accent')
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        from ui.widgets.title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, title="Settings", show_minimize=False, show_maximize=False)
        main_layout.addWidget(self.title_bar)
        
        content_widget = QWidget()
        main_layout.addWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("⚙")
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {text_secondary};")
        title_lbl = QLabel("Pengaturan")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {text_primary};")
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Card
        card = QFrame()
        card.setObjectName("SettingsCard")
        card.setStyleSheet(f"""
            QFrame#SettingsCard {{
                background-color: {ThemeManager.get_color('bg_surface')};
                border-radius: 8px;
                border: 1px solid {ThemeManager.get_color('border')};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        
        folder_label = QLabel("Output Folder Utama:")
        folder_label.setStyleSheet(f"font-weight: bold; color: {text_primary};")
        card_layout.addWidget(folder_label)
        
        input_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setText(AppSettings.get_default_folder())
        self.folder_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                background-color: {ThemeManager.get_color('bg_main')};
                color: {text_primary};
                border: 1px solid {ThemeManager.get_color('border')};
                border-radius: 6px;
                font-size: 13px;
            }}
        """)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 16px;
                background-color: transparent;
                color: {text_secondary};
                border: 1px solid {ThemeManager.get_color('border')};
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_main')};
                color: {text_primary};
            }}
        """)
        browse_btn.clicked.connect(self._on_browse)
        
        input_layout.addWidget(self.folder_input)
        input_layout.addWidget(browse_btn)
        card_layout.addLayout(input_layout)
        
        desc = QLabel(
            "Struktur folder otomatis:\n"
            " └─ kompilasi/ {judul}/\n"
            " └─ playlist/ {judul}/"
        )
        desc.setStyleSheet(f"font-size: 11px; color: {text_secondary}; margin-top: 10px;")
        card_layout.addWidget(desc)
        
        layout.addWidget(card)
        layout.addStretch()
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Batal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(browse_btn.styleSheet())
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Simpan Pengaturan")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 24px;
                background-color: {accent};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('accent_hover')};
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def _on_browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Output Folder", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)
            
    def _on_save(self):
        folder = self.folder_input.text()
        if folder:
            AppSettings.set_default_folder(folder)
            os.makedirs(folder, exist_ok=True)
            self.accept()

    def accept(self):
        self._fade_out_and_close(self._do_accept)

    def _do_accept(self):
        QDialog.accept(self)

    def reject(self):
        self._fade_out_and_close(self._do_reject)

    def _do_reject(self):
        QDialog.reject(self)
        
    def _fade_out_and_close(self, callback):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        if getattr(self, "_fade_anim_slot", None):
            try:
                self._fade_anim.finished.disconnect(self._fade_anim_slot)
            except Exception:
                pass
        self._fade_anim_slot = callback
        self._fade_anim.finished.connect(self._fade_anim_slot)
        self._fade_anim.start()

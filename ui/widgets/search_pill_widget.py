from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QVariantAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QColor, QAction
from ui.themes.theme_manager import ThemeManager

class SearchPillWidget(QWidget):
    """
    A responsive premium AI-style search bar with integrated icon and button.
    """
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        self.setObjectName("SearchPillWidget")
        self.setMinimumWidth(500)
        self.setMaximumWidth(950)
        self.setFixedHeight(64)
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.bg_surface = ThemeManager.get_color("bg_surface")
        self.border = ThemeManager.get_color("border")
        self.border_hover = ThemeManager.get_color("border_hover")
        self.border_accent = ThemeManager.get_color("accent_border")
        self.accent = ThemeManager.get_color("accent")
        self.accent_light = ThemeManager.get_color("accent_light")
        self.accent_muted = ThemeManager.get_color("accent_muted")
        
        self.setStyleSheet(f"""
            QWidget#SearchPillWidget {{
                background-color: {self.bg_surface};
                border: 1px solid {self.border_hover};
                border-radius: 32px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 8, 8) # Left padding handles the QLineEdit
        layout.setSpacing(12)

        # Search Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Cari lagu, artis, playlist, atau tempel URL YouTube...")

        text_primary = ThemeManager.get_color("text_primary")
        text_muted = ThemeManager.get_color("text_muted")
        
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {text_primary};
                font-size: 16px;
                padding-left: 8px;
            }}
            QLineEdit::placeholder {{
                color: {text_muted};
            }}
        """)
        layout.addWidget(self.input_field)

        # Integrated Search Button
        self.search_btn = QPushButton("Cari")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setFixedSize(120, 48)
        
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent};
                border: none;
                border-radius: 24px;
                color: white;
                font-size: 15px;
                font-weight: 500;
            }}
        """)
        layout.addWidget(self.search_btn)

        # Focus glow effect
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(0)
        try:
            rgba_vals = self.accent_muted.replace('rgba(', '').replace(')', '').split(',')
            color = QColor(int(rgba_vals[0]), int(rgba_vals[1]), int(rgba_vals[2]), 0)
        except:
            color = QColor(232, 99, 26, 0)
            
        self.shadow_effect.setColor(color)
        self.shadow_effect.setOffset(0, 0)
        self.shadow_effect.setEnabled(True)
        self.setGraphicsEffect(self.shadow_effect)

        # Connections
        self.input_field.returnPressed.connect(self._on_search)
        self.search_btn.clicked.connect(self._on_search)
        
        # Event Filters for Hover/Focus tracking
        self.input_field.installEventFilter(self)
        self.search_btn.installEventFilter(self)

    def _setup_animations(self):
        # Focus Shadow Animation
        self.focus_anim = QPropertyAnimation(self.shadow_effect, b"blurRadius")
        self.focus_anim.setDuration(250)
        self.focus_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # We can't animate CSS directly easily without QVariantAnimation
        self.btn_color_anim = QVariantAnimation(self)
        self.btn_color_anim.setDuration(200)
        self.btn_color_anim.valueChanged.connect(self._update_btn_color)
        
        self._current_btn_color = QColor(self.accent)

    def _update_btn_color(self, color):
        self._current_btn_color = color
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: none;
                border-radius: 24px;
                color: white;
                font-size: 15px;
                font-weight: 500;
            }}
        """)

    def eventFilter(self, obj, event):
        if obj == self.input_field:
            if event.type() == event.Type.FocusIn:
                self.focus_anim.stop()
                self.focus_anim.setStartValue(self.shadow_effect.blurRadius())
                self.focus_anim.setEndValue(20)
                self.shadow_effect.setColor(QColor(232, 99, 26, 80))
                self.focus_anim.start()
            elif event.type() == event.Type.FocusOut:
                self.focus_anim.stop()
                self.focus_anim.setStartValue(self.shadow_effect.blurRadius())
                self.focus_anim.setEndValue(0)
                self.focus_anim.start()
        elif obj == self.search_btn:
            if event.type() == event.Type.Enter:
                self.btn_color_anim.stop()
                self.btn_color_anim.setStartValue(self._current_btn_color)
                self.btn_color_anim.setEndValue(QColor(self.accent_light))
                self.btn_color_anim.start()
            elif event.type() == event.Type.Leave:
                self.btn_color_anim.stop()
                self.btn_color_anim.setStartValue(self._current_btn_color)
                self.btn_color_anim.setEndValue(QColor(self.accent))
                self.btn_color_anim.start()
            elif event.type() == event.Type.MouseButtonPress:
                self.btn_color_anim.stop()
                self.search_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {ThemeManager.get_color('text_secondary')};
                        border: none;
                        border-radius: 24px;
                        color: white;
                        font-size: 15px;
                        font-weight: 500;
                    }}
                """)
            elif event.type() == event.Type.MouseButtonRelease:
                self._update_btn_color(QColor(self.accent_light))
                
        return super().eventFilter(obj, event)

    def _on_search(self):
        query = self.input_field.text().strip()
        if query:
            self.search_requested.emit(query)
            
    def set_text(self, text):
        self.input_field.setText(text)
        
    def set_enabled(self, enabled):
        self.input_field.setEnabled(enabled)
        self.search_btn.setEnabled(enabled)

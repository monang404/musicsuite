from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QSizePolicy, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from ui.themes.theme_manager import ThemeManager

class ActivityStreamWidget(QWidget):
    """
    Claude-style minimal AI Activity Stream.
    Displays a title and a dynamic spinner status line.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        
        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_idx = 0
        
        self._setup_ui()
        
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(80)
        self._spinner_timer.timeout.connect(self._update_spinner)
        
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(3000)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._revert_to_idle)
        
        self._render_idle()

    def _setup_ui(self):
        self.setObjectName("ActivityStreamWidget")
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_StyledBackground, False)
        
        self.text_secondary = ThemeManager.get_color("text_secondary")
        self.text_muted = ThemeManager.get_color("text_muted")
        self.accent = ThemeManager.get_color("accent")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 0, 0, 0)
        self.main_layout.setSpacing(4)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.status_layout = QHBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(6)
        
        self.spinner_label = QLabel()
        self.spinner_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 13px; font-family: monospace;")
        self.status_layout.addWidget(self.spinner_label)
        
        self.text_label = QLabel()
        self.text_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 13px;")
        self.status_layout.addWidget(self.text_label)
        
        self.status_layout.addStretch()
        self.main_layout.addLayout(self.status_layout)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

    def _animate_fade(self, callback):
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(150)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.OutQuad)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(150)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InQuad)
        
        def on_fade_out_finished():
            callback()
            self.fade_in.start()
            
        self.fade_out.finished.connect(on_fade_out_finished)
        self.fade_out.start()

    def _update_spinner(self):
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self.spinner_label.setText(self._spinner_frames[self._spinner_idx])

    def _render_idle(self):
        self.spinner_label.setText("●")
        self.spinner_label.setStyleSheet(f"color: {self.text_muted}; font-size: 13px; font-family: monospace;")
        self.text_label.setText("Siap menerima pencarian")
        self.text_label.setStyleSheet(f"color: {self.text_muted}; font-size: 13px;")

    def _render_active(self, initial_message):
        self.spinner_label.setStyleSheet(f"color: {self.accent}; font-size: 13px; font-family: monospace;")
        self.text_label.setText(initial_message)
        self.text_label.setStyleSheet(f"color: {self.accent}; font-size: 13px;")

    def set_active_state(self):
        if not self._is_active:
            self._is_active = True
            self._idle_timer.stop()
            self._spinner_timer.start()
            self._animate_fade(lambda: self._render_active("Memahami maksud pencarian..."))

    def add_progress(self, message: str):
        if not self._is_active:
            return
        self.text_label.setText(message)

    def set_idle_state(self):
        if self._is_active:
            self._is_active = False
            self._spinner_timer.stop()
            self.spinner_label.setText("✔")
            self.spinner_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 13px; font-family: monospace;")
            self.text_label.setText("Pencarian selesai.")
            self.text_label.setStyleSheet(f"color: {self.text_secondary}; font-size: 13px;")
            self._idle_timer.start()
            
    def _revert_to_idle(self):
        self._animate_fade(self._render_idle)

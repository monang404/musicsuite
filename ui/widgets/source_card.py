from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.quality_result import QualityResult
from ui.themes.theme_manager import ThemeManager

class SourceCard(QWidget):
    """
    UI representation of a search result source.
    """
    clicked = Signal(object) # CompilationVideo

    def __init__(self, source: CompilationVideo, quality: QualityResult = None, parent=None):
        super().__init__(parent)
        self.source = source
        self.quality = quality
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        border_color = ThemeManager.get_color("text_muted")
        bg_color = ThemeManager.get_color("bg_surface")
        border_hover = ThemeManager.get_color("text_secondary")
        bg_hover = ThemeManager.get_color("bg_hover")
        text_primary = ThemeManager.get_color("text_primary")
        text_secondary = ThemeManager.get_color("text_secondary")
        success = ThemeManager.get_color("success")
        warning = ThemeManager.get_color("warning")
        danger = ThemeManager.get_color("danger")

        self.setStyleSheet(f"""
            SourceCard {{
                border: 1px solid {border_color};
                border-radius: 5px;
                background-color: {bg_color};
                margin-bottom: 5px;
            }}
            SourceCard:hover {{
                border: 1px solid {border_hover};
                background-color: {bg_hover};
            }}
        """)

        title_label = QLabel(self.source.title)
        title_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_primary};")
        title_label.setWordWrap(True)
        
        details_layout = QHBoxLayout()
        channel_label = QLabel(f"Channel: {self.source.channel}")
        channel_label.setStyleSheet(f"color: {text_secondary};")
        
        duration_label = QLabel(f"Duration: {self.source.duration}s")
        duration_label.setStyleSheet(f"color: {text_secondary};")

        details_layout.addWidget(channel_label)
        details_layout.addWidget(duration_label)
        
        if self.source.track_count > 0:
            tracks_label = QLabel(f"Tracks: {self.source.track_count}")
            tracks_label.setStyleSheet(f"color: {text_secondary};")
            details_layout.addWidget(tracks_label)

        details_layout.addStretch()

        if self.quality:
            score_label = QLabel(f"Score: {self.quality.score}/100")
            if self.quality.score >= 80:
                score_label.setStyleSheet(f"color: {success}; font-weight: bold;")
            elif self.quality.score >= 50:
                score_label.setStyleSheet(f"color: {warning}; font-weight: bold;")
            else:
                score_label.setStyleSheet(f"color: {danger}; font-weight: bold;")
            details_layout.addWidget(score_label)

        layout.addWidget(title_label)
        layout.addLayout(details_layout)
        
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.source)

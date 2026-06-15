from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.quality_result import QualityResult

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
        self.setStyleSheet("""
            SourceCard {
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #222;
                margin-bottom: 5px;
            }
            SourceCard:hover {
                border: 1px solid #666;
                background-color: #333;
            }
        """)

        title_label = QLabel(self.source.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        title_label.setWordWrap(True)
        
        details_layout = QHBoxLayout()
        channel_label = QLabel(f"Channel: {self.source.channel}")
        channel_label.setStyleSheet("color: #aaaaaa;")
        
        duration_label = QLabel(f"Duration: {self.source.duration}s")
        duration_label.setStyleSheet("color: #aaaaaa;")

        details_layout.addWidget(channel_label)
        details_layout.addWidget(duration_label)
        
        if self.source.track_count > 0:
            tracks_label = QLabel(f"Tracks: {self.source.track_count}")
            tracks_label.setStyleSheet("color: #aaaaaa;")
            details_layout.addWidget(tracks_label)

        details_layout.addStretch()

        if self.quality:
            score_label = QLabel(f"Score: {self.quality.score}/100")
            if self.quality.score >= 80:
                score_label.setStyleSheet("color: #55ff55; font-weight: bold;")
            elif self.quality.score >= 50:
                score_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
            else:
                score_label.setStyleSheet("color: #ff5555; font-weight: bold;")
            details_layout.addWidget(score_label)

        layout.addWidget(title_label)
        layout.addLayout(details_layout)
        
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.source)

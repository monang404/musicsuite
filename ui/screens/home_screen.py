from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from ui.screens.base_screen import BaseScreen
from ui.viewmodels.home_vm import HomeViewModel
from ui.widgets.search_pill_widget import SearchPillWidget
from ui.widgets.activity_stream_widget import ActivityStreamWidget
from ui.themes.theme_manager import ThemeManager

class HomeScreen(BaseScreen):
    """
    A premium AI-style landing page with an ambient animated background,
    fluid micro-animations, and a highly responsive layout.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bind_viewmodel(HomeViewModel())
        self._check_dependencies()

    def _check_dependencies(self):
        from ui.core.service_container import ServiceContainer
        deps = ServiceContainer().dependency_service.get_dependency_status()
        missing = [dep for dep, available in deps.items() if not available]
        if missing:
            self.search_pill.set_enabled(False)
            self.error_label.setText("Search disabled due to missing system dependencies.")
            self.error_label.show()

    def _setup_ui(self):
        # Main content container to allow opacity fading
        self.content_container = QWidget(self)
        self.main_layout = QVBoxLayout(self.content_container)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setContentsMargins(24, 32, 24, 32)
        self.main_layout.setSpacing(0)

        # Set up a layout for the screen itself to hold the container
        self.screen_layout = QVBoxLayout(self)
        self.screen_layout.setContentsMargins(0, 0, 0, 0)
        self.screen_layout.addWidget(self.content_container)

        # Add top stretch for perfect centering (approx 45% visual center offset by elements below)
        self.main_layout.addStretch(4)

        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(18)
        title_layout.setAlignment(Qt.AlignCenter)
        
        accent = ThemeManager.get_color("accent")
        text_primary = ThemeManager.get_color("text_primary")
        text_secondary = ThemeManager.get_color("text_secondary")
        text_muted = ThemeManager.get_color("text_muted")
        
        self.title_label = QLabel(f"<span style='color:{accent}'>♪</span> Music Suite")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"font-size: 48px; font-weight: 700; color: {text_primary};")
        
        self.tagline_label = QLabel("Find music compilations and playlists")
        self.tagline_label.setAlignment(Qt.AlignCenter)
        self.tagline_label.setStyleSheet(f"font-size: 16px; color: {text_secondary}; opacity: 0.8;")
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.tagline_label)
        self.main_layout.addLayout(title_layout)
        self.main_layout.addSpacing(40)

        # Search Bar Area (Responsive)
        self.search_pill = SearchPillWidget()
        self.main_layout.addWidget(self.search_pill, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(16)

        # AI Activity Stream (replaces old QProgressBar)
        self.activity_stream = ActivityStreamWidget()
        self.main_layout.addWidget(self.activity_stream, alignment=Qt.AlignCenter)

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #ff5555; font-weight: bold;")
        self.error_label.hide()
        self.main_layout.addWidget(self.error_label)

        # Add bottom stretch (weight 5 pushes content slightly above true center, ~45% from top)
        self.main_layout.addStretch(5)

    def showEvent(self, event):
        """Fade-in animation when the screen is shown."""
        super().showEvent(event)
        
        # Create a fresh effect on every showEvent to prevent C++ deleted object crashes
        self.opacity_effect = QGraphicsOpacityEffect(self.content_container)
        self.opacity_effect.setOpacity(0.0)
        self.content_container.setGraphicsEffect(self.opacity_effect)
        
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(600)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_anim.finished.connect(lambda: self.content_container.setGraphicsEffect(None))
        self.fade_anim.start()

    def hideEvent(self, event):
        super().hideEvent(event)

    def resizeEvent(self, event):
        """
        Responsive resizing: Maintain 70% width for search components,
        clamped between 500px and 1100px.
        """
        super().resizeEvent(event)
        
        # Calculate dynamic width
        target_width = int(self.width() * 0.70)
        clamped_width = max(500, min(950, target_width))
        
        # Apply responsive widths
        self.search_pill.setFixedWidth(clamped_width)
        self.activity_stream.setFixedWidth(clamped_width)

    def connect_signals(self):
        # UI -> ViewModel
        self.search_pill.search_requested.connect(self._on_search_requested)
        
        # ViewModel -> UI
        vm: HomeViewModel = self.viewmodel
        vm.search_initiated.connect(self._on_search_initiated)
        vm.search_completed.connect(self._on_search_completed)
        vm.search_failed.connect(self._on_search_failed)
        vm.search_progress_updated.connect(self._on_progress_updated)

    def _on_search_requested(self, query):
        if query:
            self.viewmodel.submit_query(query)

    def _on_search_initiated(self, query):
        self.error_label.hide()
        self.activity_stream.set_active_state()
        self.search_pill.set_enabled(False)

    def _on_progress_updated(self, percent: float, message: str):
        self.activity_stream.add_progress(message)

    def _on_search_completed(self, results):
        self.activity_stream.set_idle_state()
        self.search_pill.set_enabled(True)
        # Pass query from recent searches (first item is the latest)
        query = self.viewmodel.recent_searches[0] if self.viewmodel.recent_searches else ""
        self.navigate_requested.emit("RESULTS", {"results": results, "query": query})

    def _on_search_failed(self, error: str):
        self.activity_stream.set_idle_state()
        self.error_label.setText(error)
        self.error_label.show()
        self.search_pill.set_enabled(True)

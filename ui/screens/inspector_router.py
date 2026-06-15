from PySide6.QtWidgets import QVBoxLayout, QStackedWidget
from ui.screens.base_screen import BaseScreen
from ui.screens.compilation_inspector_screen import CompilationInspectorScreen
from ui.screens.playlist_inspector_screen import PlaylistInspectorScreen

class InspectorRouter(BaseScreen):
    """
    Acts as a router for the INSPECTOR route.
    Delegates to CompilationInspectorScreen or PlaylistInspectorScreen
    based on the source's entity_type.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.connect_signals()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        self.compilation_screen = CompilationInspectorScreen(self)
        self.playlist_screen = PlaylistInspectorScreen(self)
        
        self.stacked_widget.addWidget(self.compilation_screen)
        self.stacked_widget.addWidget(self.playlist_screen)

    def connect_signals(self):
        # Forward navigation requests from child screens
        self.compilation_screen.navigate_requested.connect(self.navigate_requested.emit)
        self.playlist_screen.navigate_requested.connect(self.navigate_requested.emit)

    def on_navigated(self, **kwargs):
        source = kwargs.get("source")
        if not source:
            return
            
        entity_type = getattr(source, "entity_type", "compilation")
        
        if entity_type == "playlist":
            self.stacked_widget.setCurrentWidget(self.playlist_screen)
            self.playlist_screen.on_navigated(**kwargs)
        else:
            self.stacked_widget.setCurrentWidget(self.compilation_screen)
            self.compilation_screen.on_navigated(**kwargs)

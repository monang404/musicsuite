from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel

class BaseScreen(QWidget):
    """
    Base class for all application screens.
    Enforces a standard lifecycle and viewmodel binding pattern.
    """
    
    # Standardized signal to request navigation with an optional payload
    navigate_requested = Signal(str, dict)

    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewmodel: BaseViewModel = None
        
    def bind_viewmodel(self, viewmodel: BaseViewModel):
        """
        Binds the ViewModel to the screen.
        This must be called during initialization or before the screen is navigated to.
        """
        self.viewmodel = viewmodel
        if QWidget.layout(self) is None:
            if hasattr(self, '_setup_ui'):
                self._setup_ui()
            elif hasattr(self, 'setup_ui'):
                self.setup_ui()
            elif hasattr(self, '_build_ui'):
                self._build_ui()
        self.connect_signals()
        
    def connect_signals(self):
        """
        Connects Qt signals from UI elements to ViewModel commands,
        and ViewModel state changes to UI update slots.
        Override this in subclasses.
        """
        pass
        
    def on_navigated(self, **kwargs):
        """
        Lifecycle hook called by the Router when this screen becomes active.
        Provides dynamic context via kwargs.
        Override this in subclasses to react to navigation events.
        """
        pass


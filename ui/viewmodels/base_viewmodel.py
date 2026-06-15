from PySide6.QtCore import QObject, Signal

class BaseViewModel(QObject):
    """
    Base class for all ViewModels in the application.
    Provides standard signaling for state changes and error handling.
    """
    
    # Common signals that all ViewModels can emit
    state_changed = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_loading = False
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
        
    @is_loading.setter
    def is_loading(self, value: bool):
        if self._is_loading != value:
            self._is_loading = value
            self.state_changed.emit()


from PySide6.QtCore import QObject, Signal
from ui.router import Router

class NavigationManager(QObject):
    """
    Coordinates navigation events and acts as a central hub for routing requests.
    Decouples UI components from directly referencing the Router.
    """
    
    # Emitted when navigation occurs. Useful for updating sidebar state.
    navigated = Signal(str)
    
    def __init__(self, router: Router, parent=None):
        super().__init__(parent)
        self._router = router
        
    def goto(self, route_name: str, **kwargs):
        """
        Requests navigation to a specific route.
        """
        self._router.navigate(route_name, **kwargs)
        self.navigated.emit(route_name)
        
    def current_route(self) -> str:
        """
        Gets the currently active route name.
        """
        return self._router.current_route()


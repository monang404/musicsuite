from typing import Dict, Type
from PySide6.QtWidgets import QStackedWidget, QWidget

class Router:
    """
    Manages navigation between different screens in the application.
    Uses a QStackedWidget to handle transitions.
    """
    
    def __init__(self, stacked_widget: QStackedWidget):
        self._stacked_widget = stacked_widget
        self._screens: Dict[str, QWidget] = {}
        
    def register_screen(self, route_name: str, screen_widget: QWidget):
        """
        Registers a new screen widget with a route name.
        """
        if route_name in self._screens:
            raise ValueError(f"Screen with route name '{route_name}' is already registered.")
            
        self._screens[route_name] = screen_widget
        self._stacked_widget.addWidget(screen_widget)
        
    def navigate(self, route_name: str, **kwargs):
        """
        Navigates to the specified screen.
        Optionally passes kwargs to the screen's load/update method if it exists.
        """
        if route_name not in self._screens:
            raise ValueError(f"Route '{route_name}' not found.")
            
        target_widget = self._screens[route_name]
        self._stacked_widget.setCurrentWidget(target_widget)
        
        # If the widget has an on_navigated method, call it to pass context
        if hasattr(target_widget, 'on_navigated'):
            target_widget.on_navigated(**kwargs)
            
    def current_route(self) -> str:
        """
        Returns the name of the currently active route.
        """
        current_widget = self._stacked_widget.currentWidget()
        for route, widget in self._screens.items():
            if widget == current_widget:
                return route
        return ""


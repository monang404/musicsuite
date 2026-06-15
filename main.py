import sys
import logging
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.screens.home_screen import HomeScreen
from ui.screens.results_screen import ResultsScreen
from ui.screens.inspector_router import InspectorRouter
from ui.screens.results_center_screen import ResultsCenterScreen

# Configure root logger to only show ERRORs in terminal
logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")

def main():
    app = QApplication(sys.argv)
    
    from ui.themes.theme_manager import ThemeManager
    ThemeManager.apply_theme(app)
    
    window = MainWindow()
    
    # Register screens
    window.register_screen("HOME", HomeScreen(window), "Search")
    window.register_screen("RESULTS", ResultsScreen(window))
    window.register_screen("INSPECTOR", InspectorRouter(window))
    window.register_screen("RESULTS_CENTER", ResultsCenterScreen(window), "History")
    
    # Set initial screen
    window.nav_manager.goto("HOME")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

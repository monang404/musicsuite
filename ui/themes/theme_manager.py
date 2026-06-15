import os
from PySide6.QtWidgets import QApplication

class ThemeManager:
    """
    Manages the application theme and styling.
    Integrates with the existing theme system.
    """
    
    @staticmethod
    def apply_theme(app=None):
        """
        Applies the global stylesheet and theme to the QApplication.
        """
        if app is None:
            app = QApplication.instance()
            
        if app:
            qss_path = os.path.join(os.path.dirname(__file__), "base_stylesheet.qss")
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss = f.read()
                app.setStyleSheet(qss)
            except Exception as e:
                print(f"Failed to load stylesheet: {e}")
    
    @staticmethod
    def get_color(color_name: str) -> str:
        """
        Retrieves a color from the theme.
        """
        colors = {
            "bg_main": "#22211f",
            "bg_surface": "#2a2926",
            "bg_card": "#32302d",
            "bg_sidebar": "#1f1d1c",
            "accent": "#e8631a",
            "accent_light": "#f07a35",
            "accent_muted": "rgba(232,99,26,0.15)",
            "accent_border": "rgba(232,99,26,0.35)",
            "text_primary": "#e8e6e0",
            "text_secondary": "#9b9890",
            "text_muted": "#6b6965",
            "border": "rgba(255,255,255,0.07)",
            "border_hover": "rgba(255,255,255,0.13)",
            "bg_hover": "#3a3835",
            "success": "#3da068",
            "success_bg": "rgba(61,160,104,0.12)",
            "warning": "#d4a944",
            "warning_bg": "rgba(212,169,68,0.12)",
            "danger": "#d94444",
            "danger_bg": "rgba(217,68,68,0.12)",
            "info": "#4a90d9",
            "info_bg": "rgba(74,144,217,0.12)",
            "accent_hover": "#f07a35",
            "badge_compilation_bg": "rgba(232,99,26,0.12)",
            "badge_compilation_fg": "#e8631a",
            "badge_playlist_bg": "rgba(155,152,144,0.12)",
            "badge_playlist_fg": "#9b9890",
        }
        
        if color_name not in colors:
            is_debug = os.environ.get("DEBUG", "0") == "1"
            if is_debug:
                raise AssertionError(f"Color key '{color_name}' not found in ThemeManager")
            print(f"Warning: Color '{color_name}' missing, falling back to #FFFFFF")
            
        return colors.get(color_name, "#FFFFFF")

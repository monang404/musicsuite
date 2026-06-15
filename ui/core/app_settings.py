import os
from PySide6.QtCore import QSettings

class AppSettings:
    """Simple settings manager for the application."""
    
    _KEY_DEFAULT_FOLDER = "output/default_folder"
    
    @staticmethod
    def get_default_folder() -> str:
        settings = QSettings("MusicSuite", "MusicSuite")
        default = os.path.join(os.path.expanduser("~"), "Music", "MusicSuite")
        return settings.value(AppSettings._KEY_DEFAULT_FOLDER, default)
    
    @staticmethod
    def set_default_folder(folder: str):
        settings = QSettings("MusicSuite", "MusicSuite")
        settings.setValue(AppSettings._KEY_DEFAULT_FOLDER, folder)

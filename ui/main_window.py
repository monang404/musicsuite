from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from ui.router import Router
from ui.navigation.navigation_manager import NavigationManager
from ui.themes.theme_manager import ThemeManager

class MainWindow(QMainWindow):
    """
    The main application window.
    Provides the core layout including sidebar, titlebar, and main content area.
    Manages screen transitions via Router and NavigationManager.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Suite")
        self.resize(900, 600)
        
        import os
        from PySide6.QtGui import QIcon
        icon_path = os.path.join("assets", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Apply Base Theme
        ThemeManager.apply_theme(self)
        self.setObjectName("MainWindowRoot")
        self.setStyleSheet(f"""
            QMainWindow#MainWindowRoot {{
                border: 1px solid {ThemeManager.get_color('border')};
                background-color: {ThemeManager.get_color('bg_main')};
            }}
            QWidget {{
                color: {ThemeManager.get_color('text_primary')};
            }}
        """)
        
        # Setup Core Architecture
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self._setup_ui()
        self._setup_navigation()
        self._check_dependencies()
        
    def _check_dependencies(self):
        from ui.core.service_container import ServiceContainer
        deps = ServiceContainer().dependency_service.get_dependency_status()
        missing = [dep for dep, available in deps.items() if not available]
        if missing:
            self.error_banner.setText(f"Missing critical dependencies: {', '.join(missing)}. Search, Download, and Split features are disabled.")
            self.error_banner.show()
            
    def _setup_ui(self):
        """
        Builds the foundational layout: Topbar + Main Content Area.
        """
        central_widget = QWidget()
        central_widget.setObjectName("MainCentralWidget")
        central_widget.setStyleSheet("#MainCentralWidget { background-color: transparent; }")
        self.setCentralWidget(central_widget)
        
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        self.error_banner = QLabel()
        self.error_banner.setStyleSheet("background-color: #ff4444; color: white; padding: 10px; font-weight: bold;")
        self.error_banner.setAlignment(Qt.AlignCenter)
        self.error_banner.hide()
        outer_layout.addWidget(self.error_banner)
        
        # Unified Custom Title Bar & Topbar
        from ui.widgets.title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, title="♪ Music Suite")
        outer_layout.addWidget(self.title_bar)
        
        # Navigation Buttons Layout
        self.nav_buttons_layout = QHBoxLayout()
        self.nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_buttons_layout.setSpacing(8)
        self.nav_buttons_layout.setAlignment(Qt.AlignVCenter)
        self.title_bar.right_layout.addLayout(self.nav_buttons_layout)
        
        # Settings button
        import os
        from ui.widgets.sidebar_nav_button import SidebarNavButton
        settings_icon = os.path.join("assets", "icons", "icon_settings.svg")
        self.settings_btn = SidebarNavButton(settings_icon, tooltip="Settings")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        self.title_bar.right_layout.addWidget(self.settings_btn)
        
        # Main Content Area (Stacked Widget)
        self.content_area = QStackedWidget()
        outer_layout.addWidget(self.content_area, 1) # content takes remaining space
        
        # Size Grip
        from PySide6.QtWidgets import QSizeGrip
        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        grip_layout.addWidget(grip)
        outer_layout.addLayout(grip_layout)
        

        
    def _on_settings_clicked(self):
        from ui.screens.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def _setup_navigation(self):
        """
        Initializes the router and navigation manager.
        """
        self.router = Router(self.content_area)
        self.nav_manager = NavigationManager(self.router)
        self.nav_manager.navigated.connect(self._on_navigated)
        
    def register_screen(self, route_name: str, screen_widget: QWidget, sidebar_label: str = None):
        """
        Registers a screen into the routing architecture.
        Optionally adds an icon navigation button to the sidebar.
        """
        self.router.register_screen(route_name, screen_widget)
        
        # Automatically connect the navigation signal if the screen supports it
        if hasattr(screen_widget, 'navigate_requested'):
            screen_widget.navigate_requested.connect(self._on_screen_navigate_requested)
        
        if sidebar_label:
            import os
            from ui.widgets.sidebar_nav_button import SidebarNavButton
            
            label_lower = sidebar_label.lower()
            if "search" in label_lower:
                icon_name = "icon_search.svg"
            elif "queue" in label_lower:
                icon_name = "icon_queue.svg"
            elif "history" in label_lower or "result" in label_lower:
                icon_name = "icon_results.svg"
            else:
                icon_name = "icon_search.svg"
                
            icon_path = os.path.join("assets", "icons", icon_name)
            btn = SidebarNavButton(icon_path, tooltip=sidebar_label)
            
            if not hasattr(self, "_sidebar_buttons"):
                self._sidebar_buttons = {}
            self._sidebar_buttons[route_name] = btn
            
            btn.clicked.connect(lambda: self.nav_manager.goto(route_name))
            self.nav_buttons_layout.addWidget(btn, 0, Qt.AlignVCenter)
            
            if "queue" in label_lower:
                from ui.widgets.sidebar_badge import SidebarBadge
                self.queue_badge = SidebarBadge(btn)
                from ui.core.service_container import ServiceContainer
                ServiceContainer().queue_service.add_listener(self._on_queue_event)
                self._update_queue_badge()
            
    def _on_screen_navigate_requested(self, route_name: str, payload: dict):
        """
        Slot to handle navigation requests emitted from screens.
        """
        self.nav_manager.goto(route_name, **payload)

    from PySide6.QtCore import Slot
    
    def _on_queue_event(self, event_type, payload):
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self, "_update_queue_badge", Qt.QueuedConnection)

    @Slot()
    def _update_queue_badge(self):
        from ui.core.service_container import ServiceContainer
        from services.queue_service import JobStatus
        queue_service = ServiceContainer().queue_service
        jobs = queue_service.get_all_jobs()
        active_count = sum(1 for j in jobs if j.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED])
        if hasattr(self, "queue_badge"):
            self.queue_badge.set_count(active_count)

    def _on_navigated(self, route_name: str):
        """
        Slot called when navigation occurs. Updates active states of sidebar buttons.
        """
        parent_route = None
        if route_name in ["HOME", "RESULTS", "INSPECTOR"]:
            parent_route = "HOME"
        elif route_name in ["RESULTS_CENTER"]:
            parent_route = "RESULTS_CENTER"
            
        if hasattr(self, "_sidebar_buttons"):
            for r_name, btn in self._sidebar_buttons.items():
                btn.set_active(r_name == parent_route)

    def showEvent(self, event):
        super().showEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)

    def closeEvent(self, event):
        """
        Handles the application close request by orchestrating a graceful shutdown.
        - Cancels all queue jobs
        - Cancels and waits for active background workers (5-second timeout)
          (worker cancellation automatically terminates only their specific child processes)
        - Closes the ResultStore
        - Flushes logging
        """
        import time
        import logging
        from PySide6.QtWidgets import QApplication
        from ui.core.service_container import ServiceContainer
        from ui.workers.base_worker import BaseWorker

        # Prevent further interactions
        self.setEnabled(False)
        
        # 1. Cancel queue
        ServiceContainer().queue_service.cancel_all()
        
        # 2. Cancel and wait for workers
        # Snapshot the active workers to avoid concurrent modification issues during iteration
        active_workers = list(BaseWorker.active_workers)
        for worker in active_workers:
            worker.cancel()
            
        start_time = time.time()
        while BaseWorker.active_workers and (time.time() - start_time) < 5.0:
            QApplication.processEvents()
            time.sleep(0.1)
            
        # 3. Close ResultStore
        ServiceContainer().result_store.close()
        
        # 4. Flush logs
        logging.shutdown()
            
        event.accept()


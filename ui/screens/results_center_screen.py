from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QWidget, QFrame, QSizePolicy, QSplitter,
)
from PySide6.QtCore import Qt, QTimer
from ui.screens.base_screen import BaseScreen
from ui.viewmodels.results_center_vm import ResultsCenterViewModel


class JobResultWidget(QFrame):
    """Card widget representing one historical job in a list."""

    def __init__(self, record: dict, viewmodel: ResultsCenterViewModel, parent=None):
        super().__init__(parent)
        self.record = record
        self.viewmodel = viewmodel
        from ui.themes.theme_manager import ThemeManager
        self.setStyleSheet(f"""
            JobResultWidget {{
                background-color: {ThemeManager.get_color('bg_card')};
                border-radius: 8px;
                border: none;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        from ui.themes.theme_manager import ThemeManager
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Status badge / icon
        status = self.record.get("status", "")
        import os
        from PySide6.QtGui import QIcon
        icon_lbl = QPushButton()
        icon_lbl.setFixedSize(32, 32)
        
        if status == "COMPLETED":
            icon_lbl.setIcon(QIcon(os.path.join("assets", "icons", "icon_check.svg")))
            icon_lbl.setStyleSheet(f"border: none; background-color: {ThemeManager.get_color('success_bg')}; border-radius: 16px;")
        else:
            icon_lbl.setIcon(QIcon(os.path.join("assets", "icons", "icon_cross.svg")))
            icon_lbl.setStyleSheet(f"border: none; background-color: {ThemeManager.get_color('danger_bg')}; border-radius: 16px;")
            
        layout.addWidget(icon_lbl)

        # Info block
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        title_text = self.record.get("title") or self.record.get("id", "Unknown")
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {ThemeManager.get_color('text_primary')};")

        # Format date natively
        completed_at = self.record.get("completed_at", "")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(completed_at)
            formatted_date = dt.strftime("%d %b %Y %H:%M")
        except:
            formatted_date = completed_at[:16].replace('T', ' ')

        track_count = len(self.record.get("result_files", []))
        detail_text = f"{formatted_date}  •  {track_count} track{'s' if track_count != 1 else ''}"
        
        if status == "FAILED":
            detail_text = self.record.get("error_message", "")[:80]
            
        lbl_detail = QLabel(detail_text)
        lbl_detail.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-size: 12px;")

        info_layout.addWidget(lbl_title)
        info_layout.addWidget(lbl_detail)
        layout.addLayout(info_layout, stretch=1)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        btn_style = f"""
            QPushButton {{
                padding: 6px 16px;
                background-color: {ThemeManager.get_color('bg_main')};
                color: {ThemeManager.get_color('text_secondary')};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_hover')};
                color: {ThemeManager.get_color('text_primary')};
            }}
        """

        if status == "COMPLETED":
            btn_folder = QPushButton(" Open")
            import os
            from PySide6.QtGui import QIcon
            btn_folder.setIcon(QIcon(os.path.join("assets", "icons", "icon_open.svg")))
            btn_folder.setCursor(Qt.PointingHandCursor)
            btn_folder.setStyleSheet(btn_style)
            btn_folder.clicked.connect(
                lambda: self.viewmodel.open_output_folder(self.record["id"])
            )
            btn_layout.addWidget(btn_folder)

        btn_delete = QPushButton(" Hapus")
        import os
        from PySide6.QtGui import QIcon
        btn_delete.setIcon(QIcon(os.path.join("assets", "icons", "icon_delete.svg")))
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet(btn_style)
        btn_delete.clicked.connect(
            lambda: self.viewmodel.delete_record(self.record["id"])
        )
        btn_layout.addWidget(btn_delete)
        
        layout.addLayout(btn_layout)


class ResultsCenterScreen(BaseScreen):
    """
    Results Center Screen — historical ledger of completed and failed jobs.
    Reads exclusively from ResultStore via ResultsCenterViewModel.
    Provides searching, status filtering, and folder access.
    No engines, services or workers are invoked directly.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_debounce: QTimer = QTimer(self)
        self._search_debounce.setSingleShot(True)
        self._search_debounce.setInterval(300)
        self._build_ui()
        self.bind_viewmodel(ResultsCenterViewModel())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        from ui.themes.theme_manager import ThemeManager
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────────
        header = QHBoxLayout()
        lbl_title = QLabel("Results Center")
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")
        header.addWidget(lbl_title)
        header.addStretch()

        btn_refresh = QPushButton(" Refresh")
        import os
        from PySide6.QtGui import QIcon
        btn_refresh.setIcon(QIcon(os.path.join("assets", "icons", "icon_restore.svg"))) # Or standard refresh icon, restore is close enough for now
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_primary')};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_hover')};
            }}
        """)
        btn_refresh.setObjectName("btn_refresh")
        btn_refresh.clicked.connect(self._on_refresh)

        btn_clear_all = QPushButton(" Reset Riwayat")
        import os
        from PySide6.QtGui import QIcon
        btn_clear_all.setIcon(QIcon(os.path.join("assets", "icons", "icon_delete.svg")))
        btn_clear_all.setCursor(Qt.PointingHandCursor)
        btn_clear_all.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: transparent;
                color: {ThemeManager.get_color('danger')};
                border: 1px solid {ThemeManager.get_color('danger_bg')};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('danger_bg')};
            }}
        """)
        btn_clear_all.setObjectName("btn_clear_all")
        btn_clear_all.clicked.connect(self._on_clear_all)

        header.addWidget(btn_clear_all)
        header.addWidget(btn_refresh)
        root.addLayout(header)

        # ── Toolbar: search + filter ─────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("Search by title or source…")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_primary')};
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                background-color: {ThemeManager.get_color('bg_card')};
                border: 2px solid {ThemeManager.get_color('accent_border')};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_input, stretch=1)

        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("filter_combo")
        self.filter_combo.addItems(["All", "Completed", "Failed"])
        self.filter_combo.setFixedWidth(150)
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_primary')};
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox:focus {{
                background-color: {ThemeManager.get_color('bg_card')};
                border: 2px solid {ThemeManager.get_color('accent_border')};
            }}
        """)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.filter_combo)
        root.addLayout(toolbar)

        # ── Stats bar ────────────────────────────────────────────────────
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-size: 12px; font-weight: bold;")
        root.addWidget(self.lbl_stats)

        # ── Job list ────────────────────────────
        self.list_jobs = QListWidget()
        self.list_jobs.setObjectName("list_jobs")
        self.list_jobs.setSpacing(12)
        self.list_jobs.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
        """)
        root.addWidget(self.list_jobs, stretch=1)

    # ------------------------------------------------------------------
    # BaseScreen lifecycle
    # ------------------------------------------------------------------

    def bind_viewmodel(self, viewmodel: ResultsCenterViewModel):
        super().bind_viewmodel(viewmodel)
        viewmodel.results_updated.connect(self._refresh_ui)
        viewmodel.error_occurred.connect(self._on_error)
        viewmodel.load_history()

    def on_navigated(self, **kwargs):
        if self.viewmodel:
            self.viewmodel.load_history()

    def connect_signals(self):
        self._search_debounce.timeout.connect(self._flush_search)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_refresh(self):
        if self.viewmodel:
            self.viewmodel.load_history()

    def _on_clear_all(self):
        if not self.viewmodel:
            return
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Reset Riwayat",
            "Apakah Anda yakin ingin menghapus semua riwayat hasil?\n(File fisik tidak akan terhapus).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.viewmodel.clear_all()

    def _on_search_changed(self, text: str):
        # Debounce: wait 300ms after the user stops typing
        self._search_debounce.stop()
        self._search_debounce.start()

    def _flush_search(self):
        if self.viewmodel:
            self.viewmodel.set_search_query(self.search_input.text())

    def _on_filter_changed(self, index: int):
        if not self.viewmodel:
            return
        mapping = {
            0: ResultsCenterViewModel.FILTER_ALL,
            1: ResultsCenterViewModel.FILTER_COMPLETED,
            2: ResultsCenterViewModel.FILTER_FAILED,
        }
        self.viewmodel.set_filter(mapping.get(index, ResultsCenterViewModel.FILTER_ALL))

    def _on_error(self, message: str):
        self.lbl_stats.setText(f"⚠ {message}")
        self.lbl_stats.setStyleSheet("color:#e74c3c; font-size:11px;")

    def _refresh_ui(self):
        if not self.viewmodel:
            return

        from ui.themes.theme_manager import ThemeManager

        # ── Stats bar ────────────────────────────────────────────────────
        completed = len(self.viewmodel.completed_jobs)
        failed = len(self.viewmodel.failed_jobs)
        tracks = len(self.viewmodel.exported_tracks)
        self.lbl_stats.setText(
            f"Completed: {completed}  •  Failed: {failed}  •  Tracks exported: {tracks}"
        )
        self.lbl_stats.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-size: 12px; font-weight: bold;")

        # ── Job list ─────────────────────────────────────────────────────
        self.list_jobs.clear()
        for record in self.viewmodel.visible_records:
            item = QListWidgetItem(self.list_jobs)
            widget = JobResultWidget(record, self.viewmodel)
            item.setSizeHint(widget.sizeHint())
            self.list_jobs.setItemWidget(item, widget)

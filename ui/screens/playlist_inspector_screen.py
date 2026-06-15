from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QDialog, QGraphicsOpacityEffect,
    QScrollArea
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeySequence, QShortcut
from ui.screens.base_screen import BaseScreen
from ui.viewmodels.playlist_inspector_vm import PlaylistInspectorViewModel
from ui.themes.theme_manager import ThemeManager

class SkeletonRow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"background: {ThemeManager.get_color('bg_card')}; border-radius: 4px;")
        
        # Opacity animation: 0.3 → 0.7 → 0.3, loop
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(1200)
        self._anim.setKeyValueAt(0, 0.3)
        self._anim.setKeyValueAt(0.5, 0.7)
        self._anim.setKeyValueAt(1, 0.3)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)  # infinite
        self._anim.start()
    
    def stop_animation(self):
        self._anim.stop()



class PlaylistInspectorScreen(BaseScreen):
    """
    Playlist Selector screen that displays a simplified UI for selecting
    and downloading tracks from a playlist.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bind_viewmodel(PlaylistInspectorViewModel())

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # -------------------
        # Header
        # -------------------
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back to Results")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: transparent;
                color: {ThemeManager.get_color('text_secondary')};
                border: 1px solid {ThemeManager.get_color('bg_card')};
                border-radius: 5px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_card')};
                color: {ThemeManager.get_color('text_primary')};
            }}
        """)
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        self.title_label = QLabel("Playlist")
        self.title_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")
        
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(f"font-size: 13px; color: {ThemeManager.get_color('text_secondary')};")
        
        header_text_layout.addWidget(self.title_label)
        header_text_layout.addWidget(self.subtitle_label)
        
        header_layout.addWidget(self.back_button, 0, Qt.AlignTop)
        header_layout.addSpacing(15)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        
        self.layout.addLayout(header_layout)

        # -------------------
        # Toolbar
        # -------------------
        self.toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)
        
        btn_style = f"""
            QPushButton {{
                padding: 6px 12px;
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_primary')};
                border: 1px solid {ThemeManager.get_color('bg_card')};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_card')};
            }}
        """
        
        self.select_all_btn = QPushButton("✓ Pilih Semua")
        self.select_all_btn.setStyleSheet(btn_style)
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        
        self.clear_btn = QPushButton("Bersihkan")
        self.clear_btn.setStyleSheet(btn_style)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        
        self.invert_btn = QPushButton("Balikkan Pilihan")
        self.invert_btn.setStyleSheet(btn_style)
        self.invert_btn.setCursor(Qt.PointingHandCursor)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter lagu...")
        self.search_box.setFixedWidth(250)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px 10px;
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_primary')};
                border: 1px solid {ThemeManager.get_color('bg_card')};
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ThemeManager.get_color('accent')};
            }}
        """)
        
        toolbar_layout.addWidget(self.select_all_btn)
        toolbar_layout.addWidget(self.clear_btn)
        toolbar_layout.addWidget(self.invert_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.search_box)
        
        self.layout.addWidget(self.toolbar_widget)

        # -------------------
        # Loading Skeleton View
        # -------------------
        self.skeleton_widget = QWidget()
        skeleton_layout = QVBoxLayout(self.skeleton_widget)
        skeleton_layout.setContentsMargins(0, 0, 0, 0)
        skeleton_layout.setSpacing(8)
        
        self.skeleton_rows = []
        for _ in range(4):
            row = SkeletonRow()
            self.skeleton_rows.append(row)
            skeleton_layout.addWidget(row)
        skeleton_layout.addStretch()
        
        self.skeleton_widget.hide()
        self.layout.addWidget(self.skeleton_widget, 1)

        # -------------------
        # Error View
        # -------------------
        self.error_widget = QWidget()
        error_layout = QVBoxLayout(self.error_widget)
        error_layout.setAlignment(Qt.AlignCenter)
        
        self.error_label = QLabel("Playlist tidak dapat dimuat.")
        self.error_label.setStyleSheet(f"color: {ThemeManager.get_color('text_primary')}; font-size: 16px; font-weight: bold;")
        
        err_btn_layout = QHBoxLayout()
        self.retry_button = QPushButton("Coba Lagi")
        self.retry_button.setStyleSheet(btn_style)
        self.retry_button.setCursor(Qt.PointingHandCursor)
        
        self.back_error_button = QPushButton("Kembali")
        self.back_error_button.setStyleSheet(btn_style)
        self.back_error_button.setCursor(Qt.PointingHandCursor)
        
        err_btn_layout.addWidget(self.retry_button)
        err_btn_layout.addWidget(self.back_error_button)
        
        error_layout.addWidget(self.error_label, 0, Qt.AlignCenter)
        error_layout.addSpacing(10)
        error_layout.addLayout(err_btn_layout)
        
        self.error_widget.hide()
        self.layout.addWidget(self.error_widget, 1)

        # -------------------
        # Body (List View)
        # -------------------
        self.tracks_scroll = QScrollArea()
        self.tracks_scroll.setWidgetResizable(True)
        self.tracks_scroll.setFrameShape(QScrollArea.NoFrame)
        self.tracks_scroll.setStyleSheet("background: transparent;")
        self.tracks_scroll.setMinimumHeight(0)  # Fix Bug 2: ensure it can shrink
        
        self.tracks_container = QWidget()
        self.tracks_container.setStyleSheet("background: transparent;")
        self.tracks_layout = QVBoxLayout(self.tracks_container)
        self.tracks_layout.setAlignment(Qt.AlignTop)
        self.tracks_layout.setSpacing(8)
        
        self.tracks_scroll.setWidget(self.tracks_container)
        self.tracks_scroll.hide()
        self.layout.addWidget(self.tracks_scroll, 1)

        # -------------------
        # Sticky Footer
        # -------------------
        self.footer_widget = QWidget()
        self.footer_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {ThemeManager.get_color('bg_surface')};
                border-top: 1px solid {ThemeManager.get_color('border')};
            }}
        """)
        footer_layout = QHBoxLayout(self.footer_widget)
        footer_layout.setContentsMargins(20, 14, 20, 14)
        
        self.selection_label = QLabel("0 / 0 lagu dipilih")
        self.selection_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")
        
        self.download_btn = QPushButton("Unduh Terpilih")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setMinimumHeight(38)
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0 25px;
                background-color: {ThemeManager.get_color('accent')};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('accent_hover')};
            }}
            QPushButton:disabled {{
                background-color: {ThemeManager.get_color('bg_card')};
                color: {ThemeManager.get_color('text_secondary')};
            }}
        """)
        
        footer_layout.addWidget(self.selection_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.download_btn)
        
        self.layout.addWidget(self.footer_widget)
        
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        # Ctrl+A -> Select All
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self._on_select_all)
        # Ctrl+D -> Clear Selection
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._on_clear_selection)
        # Ctrl+I -> Invert Selection
        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(self._on_invert_selection)
        # Enter -> Download
        QShortcut(QKeySequence("Return"), self).activated.connect(self._on_download_clicked)
        # Esc -> Back
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._on_back_clicked)

    def connect_signals(self):
        vm: PlaylistInspectorViewModel = self.viewmodel

        vm.state_changed.connect(self._on_state_changed)
        vm.source_loaded.connect(self._on_source_loaded)
        vm.analysis_completed.connect(self._on_analysis_completed)
        vm.analysis_failed.connect(self._on_analysis_failed)
        vm.selection_changed.connect(self._on_selection_changed)

        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_error_button.clicked.connect(self._on_back_clicked)
        self.retry_button.clicked.connect(vm.analyze_source)
        
        self.select_all_btn.clicked.connect(self._on_select_all)
        self.clear_btn.clicked.connect(self._on_clear_selection)
        self.invert_btn.clicked.connect(self._on_invert_selection)
        self.download_btn.clicked.connect(self._on_download_clicked)
        
        self.search_box.textChanged.connect(self._on_search_changed)

    def on_navigated(self, **kwargs):
        source = kwargs.get("source")
        if source:
            self.viewmodel.load_source(source)

    def _on_source_loaded(self):
        self.error_widget.hide()
        self.search_box.setText("")

    def _on_state_changed(self):
        vm: PlaylistInspectorViewModel = self.viewmodel

        if vm.is_loading:
            self.skeleton_widget.show()
            for row in self.skeleton_rows:
                row._anim.start()
            self.toolbar_widget.hide()
            self.tracks_scroll.hide()
            self.error_widget.hide()
            self.selection_label.setText("Memuat...")
            self.download_btn.setEnabled(False)
        elif vm.analysis_status == "failed":
            self.skeleton_widget.hide()
            for row in self.skeleton_rows:
                row.stop_animation()
            self.toolbar_widget.hide()
            self.tracks_scroll.hide()
            self.error_widget.show()
            self.selection_label.setText("Gagal memuat")
            self.download_btn.setEnabled(False)
        else:
            self.skeleton_widget.hide()
            for row in self.skeleton_rows:
                row.stop_animation()
            self.error_widget.hide()
            self.toolbar_widget.show()
            self.tracks_scroll.show()

        meta = vm.metadata
        if meta:
            title = meta.get("title", "Playlist")
            count = meta.get("item_count", 0)
            self.title_label.setText(title)
            
            channel = meta.get("channel", "")
            if channel:
                self.subtitle_label.setText(f"{count} lagu dari {channel}")
            else:
                self.subtitle_label.setText(f"{count} Lagu")

        if not vm.is_loading and vm.analysis_status != "failed":
            self.selection_label.setText(f"{vm.selected_count} / {vm.total_count} lagu dipilih")
            self.download_btn.setEnabled(vm.selected_count > 0)

        # Update table ONLY if ready
        if vm.analysis_status == "ready":
            self._update_table_content()

    def _on_selection_changed(self):
        vm: PlaylistInspectorViewModel = self.viewmodel
        if not vm.is_loading and vm.analysis_status != "failed":
            self.selection_label.setText(f"{vm.selected_count} / {vm.total_count} lagu dipilih")
            self.download_btn.setEnabled(vm.selected_count > 0)

        # Update checkboxes visually without rebuilding the table layout (Fix Bug 1)
        from PySide6.QtWidgets import QFrame, QCheckBox
        for i in range(self.tracks_layout.count()):
            item = self.tracks_layout.itemAt(i)
            if not item or not item.widget():
                continue
            row_frame = item.widget()
            if not isinstance(row_frame, QFrame):
                continue
            
            row_layout = row_frame.layout()
            if not row_layout:
                continue
                
            cb_item = row_layout.itemAt(0)
            if not cb_item or not isinstance(cb_item.widget(), QCheckBox):
                continue
                
            checkbox = cb_item.widget()
            idx_item = row_layout.itemAt(1)
            
            try:
                original_idx = int(idx_item.widget().text()) - 1
            except (ValueError, AttributeError):
                continue
                
            is_selected = original_idx in vm._selected_indices
            
            checkbox.blockSignals(True)
            checkbox.setChecked(is_selected)
            checkbox.blockSignals(False)
            row_frame.setObjectName("TrackRow")
            row_frame.setStyleSheet(f"""
                QFrame#TrackRow {{
                    background-color: {ThemeManager.get_color('accent_muted') if is_selected else ThemeManager.get_color('bg_surface')};
                    border-radius: 8px;
                    border: 1px solid {ThemeManager.get_color('accent_border') if is_selected else ThemeManager.get_color('border')};
                }}
                QFrame#TrackRow:hover {{
                    background-color: {ThemeManager.get_color('accent_muted') if is_selected else ThemeManager.get_color('bg_hover')};
                }}
            """)

    def _update_table_content(self):
        vm: PlaylistInspectorViewModel = self.viewmodel
        entries = vm.get_filtered_entries_with_indices()
        
        while self.tracks_layout.count():
            item = self.tracks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        from PySide6.QtWidgets import QCheckBox
        for row_idx, (original_idx, entry) in enumerate(entries):
            is_avail = vm.is_entry_available(entry)
            is_selected = original_idx in vm._selected_indices
            
            row_frame = QFrame()
            row_frame.setObjectName("TrackRow")
            row_frame.setStyleSheet(f"""
                QFrame#TrackRow {{
                    background-color: {ThemeManager.get_color('accent_muted') if is_selected else ThemeManager.get_color('bg_surface')};
                    border-radius: 8px;
                    border: 1px solid {ThemeManager.get_color('accent_border') if is_selected else ThemeManager.get_color('border')};
                }}
                QFrame#TrackRow:hover {{
                    background-color: {ThemeManager.get_color('accent_muted') if is_selected else ThemeManager.get_color('bg_hover')};
                }}
            """)
            
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(12)
            
            checkbox = QCheckBox()
            checkbox.setChecked(is_selected)
            if not is_avail:
                checkbox.setEnabled(False)
                
            checkbox.stateChanged.connect(
                lambda state, idx=original_idx: self.viewmodel.toggle_selection(idx, state == Qt.CheckState.Checked.value or state == 2)
            )
            
            idx_lbl = QLabel(f"{original_idx + 1:02d}")
            idx_lbl.setFixedWidth(24)
            idx_lbl.setAlignment(Qt.AlignCenter)
            idx_lbl.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-weight: bold; font-size: 13px;")
            
            title_text = entry.title or "Unknown Title"
            if not is_avail:
                title_text += " (Unavailable)"
            title_lbl = QLabel(title_text)
            title_lbl.setStyleSheet(f"color: {ThemeManager.get_color('text_primary')}; font-weight: 600; font-size: 13px;")
            title_lbl.setWordWrap(True)
            if not is_avail:
                title_lbl.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-weight: 600; font-size: 13px; text-decoration: line-through;")
            
            dur_str = PlaylistInspectorViewModel._format_duration(int(entry.duration)) if entry.duration else "—"
            dur_lbl = QLabel(dur_str)
            dur_lbl.setFixedWidth(80)
            dur_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            dur_lbl.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-family: monospace; font-size: 12px;")
            
            row_layout.addWidget(checkbox)
            row_layout.addWidget(idx_lbl)
            row_layout.addWidget(title_lbl, 1)
            row_layout.addWidget(dur_lbl)
            
            self.tracks_layout.addWidget(row_frame)

    def _on_analysis_completed(self):
        pass

    def _on_analysis_failed(self, error: str):
        self._on_state_changed()

    def _on_back_clicked(self):
        self.navigate_requested.emit("RESULTS", {})

    def _on_select_all(self):
        self.viewmodel.select_all()

    def _on_clear_selection(self):
        self.viewmodel.clear_selection()

    def _on_invert_selection(self):
        self.viewmodel.invert_selection()

    def _on_search_changed(self, text: str):
        self.viewmodel.filter_text = text

    def _on_download_clicked(self):
        vm: PlaylistInspectorViewModel = self.viewmodel
        if vm.selected_count == 0:
            return
            
        result = vm.download_selected()
        if result:
            source, metadata = result
            from ui.screens.process_screen import DownloadConfigDialog
            dialog = DownloadConfigDialog(source, "", metadata, self)
            dialog.config_confirmed.connect(self._on_config_confirmed)
            dialog.exec()

    def _on_config_confirmed(self, job):
        from ui.screens.download_screen import DownloadDialog
        self._download_dialog = DownloadDialog(job, parent=self.window())
        self._download_dialog.show()

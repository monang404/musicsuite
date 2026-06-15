from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTabWidget, QScrollArea, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QProgressBar, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from ui.screens.base_screen import BaseScreen
from ui.viewmodels.compilation_inspector_vm import CompilationInspectorViewModel
from ui.themes.theme_manager import ThemeManager
from ui.widgets.thinking_dots import ThinkingDots

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

class CompilationInspectorScreen(BaseScreen):
    """
    Displays detailed analysis of a selected source.
    Shows metadata, track list, timestamp preview, confidence indicators,
    duration statistics, and extraction status.

    Navigation:
        RESULTS → INSPECTOR → PROCESS
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bind_viewmodel(CompilationInspectorViewModel())

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # === HEADER ===
        header_container = QWidget()
        header_container.setStyleSheet(
            f"background: {ThemeManager.get_color('bg_main')};"
            f"border-bottom: 1px solid {ThemeManager.get_color('border')};"
        )
        header_outer = QVBoxLayout(header_container)
        header_outer.setContentsMargins(20, 16, 20, 0)
        header_outer.setSpacing(8)

        header_layout = QHBoxLayout()
        self.back_button = QPushButton("← Kembali ke Hasil")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: transparent;
                color: {ThemeManager.get_color('text_secondary')};
                border: 1px solid {ThemeManager.get_color('border')};
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_primary')};
            }}
        """)

        title = QLabel("Compilation Inspector")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")

        self.thinking_dots = ThinkingDots(prefix="Menganalisis sumber")
        self.thinking_dots.hide()

        self.status_badge = QLabel("IDLE")
        self.status_badge.setStyleSheet(f"""
            padding: 4px 12px;
            background-color: {ThemeManager.get_color('bg_surface')};
            color: {ThemeManager.get_color('text_muted')};
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)

        header_layout.addWidget(self.back_button)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.thinking_dots)
        header_layout.addWidget(self.status_badge)
        header_outer.addLayout(header_layout)

        # --- Loading Bar ---
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setFixedHeight(3)
        self.loading_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {ThemeManager.get_color('bg_surface')};
            }}
            QProgressBar::chunk {{
                background-color: {ThemeManager.get_color('accent')};
            }}
        """)
        self.loading_bar.hide()
        header_outer.addWidget(self.loading_bar)

        # --- Error Label ---
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(f"color: {ThemeManager.get_color('danger')}; font-weight: bold; padding: 8px; background: {ThemeManager.get_color('danger_bg')}; border-radius: 5px;")
        self.error_label.hide()
        header_outer.addWidget(self.error_label)
        self.layout.addWidget(header_container)

        # === SCROLL AREA ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: {ThemeManager.get_color('bg_main')}; border: none; }}
            QScrollBar:vertical {{
                background: {ThemeManager.get_color('bg_surface')};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeManager.get_color('text_muted')};
                border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background: {ThemeManager.get_color('bg_main')};")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 16, 20, 16)
        scroll_layout.setSpacing(16)

        # 1. Info Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_color('bg_card')};
                border-radius: 8px;
            }}
        """)
        info_card_layout = QVBoxLayout(self.info_card)
        info_card_layout.setContentsMargins(20, 16, 20, 16)
        info_card_layout.setSpacing(10)

        self.title_label = QLabel("—")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")

        self.subtitle_label = QLabel("—")
        self.subtitle_label.setStyleSheet(f"font-size: 12px; color: {ThemeManager.get_color('text_secondary')};")

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.tracks_count_label = self._make_detail_label("— tracks")
        self.avg_duration_label = self._make_detail_label("Avg —")
        
        self.score_label = QLabel("Score: —")
        self.score_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ThemeManager.get_color('text_muted')};")

        self.score_badge_label = QLabel("—")
        self.score_badge_label.setAlignment(Qt.AlignCenter)
        self.score_badge_label.setStyleSheet(f"""
            padding: 4px 12px;
            background-color: {ThemeManager.get_color('bg_surface')};
            color: {ThemeManager.get_color('text_muted')};
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)

        stats_layout.addWidget(self.tracks_count_label)
        
        divider1 = QLabel("|")
        divider1.setStyleSheet(f"color: {ThemeManager.get_color('border')};")
        stats_layout.addWidget(divider1)
        
        stats_layout.addWidget(self.avg_duration_label)

        divider2 = QLabel("|")
        divider2.setStyleSheet(f"color: {ThemeManager.get_color('border')};")
        stats_layout.addWidget(divider2)

        stats_layout.addWidget(self.score_label)
        stats_layout.addWidget(self.score_badge_label)
        stats_layout.addStretch()

        info_card_layout.addWidget(self.title_label)
        info_card_layout.addWidget(self.subtitle_label)
        info_card_layout.addLayout(stats_layout)
        
        self.skeleton_card = QFrame()
        self.skeleton_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_color('bg_card')};
                border-radius: 8px;
                padding: 20px;
            }}
        """)
        skeleton_card_layout = QVBoxLayout(self.skeleton_card)
        skeleton_card_layout.setSpacing(8)
        self.skeleton_rows = []
        for _ in range(3):
            row = SkeletonRow()
            self.skeleton_rows.append(row)
            skeleton_card_layout.addWidget(row)
        skeleton_card_layout.addStretch()
        self.skeleton_card.hide()

        scroll_layout.addWidget(self.info_card)
        scroll_layout.addWidget(self.skeleton_card)
        
        # 2. Indicators Row
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(15)
        
        self.chapters_indicator = self._make_indicator("Chapters", "Video memiliki marker chapter (bab) resmi dari YouTube.")
        self.timestamps_indicator = self._make_indicator("Timestamps", "Deskripsi video berisi timestamp waktu untuk pembagian lagu.")
        self.full_coverage_indicator = self._make_indicator("Full Coverage", "Timestamp mencakup sebagian besar durasi video tanpa jeda besar.")
        self.monotonic_indicator = self._make_indicator("Monotonic", "Urutan waktu timestamp berjalan maju dan berurutan secara logis.")
        self.deep_fetched_indicator = self._make_indicator("Deep Fetched", "Data metadata didapatkan melalui pengambilan yang lebih mendalam via engine.")

        indicators_layout.addWidget(self.chapters_indicator)
        indicators_layout.addWidget(self.timestamps_indicator)
        indicators_layout.addWidget(self.full_coverage_indicator)
        indicators_layout.addWidget(self.monotonic_indicator)
        indicators_layout.addWidget(self.deep_fetched_indicator)
        indicators_layout.addStretch()

        scroll_layout.addLayout(indicators_layout)

        self._info_card_effect = QGraphicsOpacityEffect(self.info_card)
        self.info_card.setGraphicsEffect(self._info_card_effect)
        self._info_card_anim = QPropertyAnimation(self._info_card_effect, b"opacity")
        self._info_card_anim.setDuration(300)
        self._info_card_anim.setStartValue(0)
        self._info_card_anim.setEndValue(1.0)

        # --- Tabbed Bottom Panel ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
                padding-top: 15px;
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                background-color: transparent;
                color: {ThemeManager.get_color('text_secondary')};
                border-bottom: 2px solid transparent;
                margin-right: 10px;
                font-weight: bold;
                font-size: 14px;
            }}
            QTabBar::tab:selected {{
                color: {ThemeManager.get_color('accent')};
                border-bottom: 2px solid {ThemeManager.get_color('accent')};
            }}
            QTabBar::tab:hover:!selected {{
                color: {ThemeManager.get_color('text_primary')};
            }}
        """)

        # Tab 1: Track Preview
        tracks_tab = QWidget()
        tracks_layout = QVBoxLayout(tracks_tab)

        self.tracks_scroll = QScrollArea()
        self.tracks_scroll.setWidgetResizable(True)
        self.tracks_scroll.setFrameShape(QScrollArea.NoFrame)
        self.tracks_scroll.setStyleSheet("background: transparent;")
        
        self.tracks_container = QWidget()
        self.tracks_container.setStyleSheet("background: transparent;")
        self.tracks_layout = QVBoxLayout(self.tracks_container)
        self.tracks_layout.setAlignment(Qt.AlignTop)
        self.tracks_layout.setSpacing(10)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tracks_scroll.setWidget(self.tracks_container)

        self.tracks_empty_label = QLabel("Tidak ada track terdeteksi.")
        self.tracks_empty_label.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-style: italic; padding: 20px;")
        self.tracks_empty_label.setAlignment(Qt.AlignCenter)

        tracks_layout.addWidget(self.tracks_scroll)
        tracks_layout.addWidget(self.tracks_empty_label)
        self.tracks_empty_label.hide()

        # Tab 2: Timestamp Editor
        timestamp_tab = QWidget()
        timestamp_layout = QVBoxLayout(timestamp_tab)

        ts_header = QHBoxLayout()
        ts_label = QLabel("Timestamps (MM:SS|Title per line)")
        ts_label.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-size: 12px;")
        self.parse_button = QPushButton("Parse / Update")
        self.parse_button.setCursor(Qt.PointingHandCursor)
        self.parse_button.setStyleSheet(f"""
            QPushButton {{
                padding: 6px 14px;
                background-color: {ThemeManager.get_color('accent')};
                color: {ThemeManager.get_color('bg_main')};
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        ts_header.addWidget(ts_label)
        ts_header.addStretch()
        ts_header.addWidget(self.parse_button)
        timestamp_layout.addLayout(ts_header)

        self.timestamp_editor = QTextEdit()
        self.timestamp_editor.setPlaceholderText("00:00|Track Title\n03:45|Another Track\n...")
        self.timestamp_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeManager.get_color('bg_main')};
                color: {ThemeManager.get_color('text_primary')};
                border: 1px solid {ThemeManager.get_color('bg_card')};
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 13px;
            }}
        """)
        timestamp_layout.addWidget(self.timestamp_editor)

        self.tabs.addTab(tracks_tab, "Track Preview")
        self.tabs.addTab(timestamp_tab, "Timestamp Editor")
        scroll_layout.addWidget(self.tabs, 1)

        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll, 1)

        # === FOOTER ===
        footer_container = QWidget()
        footer_container.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border-top: none;
            }}
        """)
        footer_layout = QHBoxLayout(footer_container)
        footer_layout.setContentsMargins(20, 12, 20, 12)

        self.process_button = QPushButton("Lanjutkan →")
        self.process_button.setCursor(Qt.PointingHandCursor)
        self.process_button.setMinimumHeight(42)
        self.process_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 30px;
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
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_muted')};
            }}
        """)
        self.process_button.setEnabled(False)

        footer_layout.addStretch()
        footer_layout.addWidget(self.process_button)
        self.layout.addWidget(footer_container)

    def connect_signals(self):
        """Connects ViewModel signals to UI slots and UI events to ViewModel commands."""
        vm: CompilationInspectorViewModel = self.viewmodel

        # ViewModel → UI
        vm.state_changed.connect(self._on_state_changed)
        vm.source_loaded.connect(self._on_source_loaded)
        vm.analysis_completed.connect(self._on_analysis_completed)
        vm.analysis_failed.connect(self._on_analysis_failed)

        # UI → ViewModel
        self.back_button.clicked.connect(self._on_back_clicked)
        self.process_button.clicked.connect(self._on_process_clicked)
        self.parse_button.clicked.connect(self._on_parse_clicked)

    def on_navigated(self, **kwargs):
        """Called when Router navigates to this screen with a source payload."""
        source = kwargs.get("source")
        if source:
            self.viewmodel.load_source(source)

    # --- UI Update Slots ---

    def _on_source_loaded(self):
        """Called when a source is initially loaded (before analysis)."""
        self.error_label.hide()

    def _on_state_changed(self):
        """Reacts to ViewModel state changes to refresh all UI elements."""
        vm: CompilationInspectorViewModel = self.viewmodel

        # Loading state
        if vm.is_loading:
            self.loading_bar.show()
            self.process_button.setEnabled(False)
            self.info_card.hide()
            self.skeleton_card.show()
            for row in self.skeleton_rows:
                row._anim.start()
            self.thinking_dots.start()
        else:
            self.loading_bar.hide()
            if self.skeleton_card.isVisible():
                self.skeleton_card.hide()
                for row in self.skeleton_rows:
                    row.stop_animation()
                self.info_card.show()
                self._info_card_anim.start()
            self.thinking_dots.stop()

        # Status badge
        self._update_status_badge(vm.analysis_status)

        # Metadata panel
        meta = vm.metadata
        if meta:
            self.title_label.setText(meta.get("title", "—"))
            channel = meta.get('channel', '—')
            duration = meta.get('duration_formatted', '—')
            views = f"{meta.get('view_count', 0):,} views"
            raw_date = meta.get('upload_date', '—')
            if len(raw_date) == 8:
                try:
                    from datetime import datetime
                    d = datetime.strptime(raw_date, "%Y%m%d")
                    upload = f"{d.day} {d.strftime('%b %Y')}"
                except Exception:
                    upload = raw_date
            else:
                upload = raw_date
            
            self.subtitle_label.setText(f"{channel} • {duration} • {views} • {upload}")
            self.tracks_count_label.setText(f"{meta.get('track_count', 0)} tracks")
            self.avg_duration_label.setText(f"Avg {meta.get('avg_track_duration_formatted', 'N/A')}")

            # Confidence indicators
            self._update_indicator(self.chapters_indicator, meta.get("has_chapters", False))
            self._update_indicator(self.timestamps_indicator, meta.get("has_timestamps", False))
            self._update_indicator(self.full_coverage_indicator, meta.get("chapters_cover_full_duration", False))
            self._update_indicator(self.monotonic_indicator, meta.get("timestamps_are_monotonic", False))
            self._update_indicator(self.deep_fetched_indicator, meta.get("is_deep_fetched", False))

        # Confidence score
        score = vm.confidence_score
        if score:
            self.score_label.setText(f"Score: {score.score}/100")
            self.score_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {score.badge_color};")
            self.score_badge_label.setText(score.label)
            self.score_badge_label.setStyleSheet(f"""
                padding: 4px 12px;
                background-color: {score.badge_color};
                color: #FFFFFF;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
            """)
        else:
            self.score_label.setText("Score: —")
            self.score_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ThemeManager.get_color('text_muted')};")
            self.score_badge_label.setText("—")
            self.score_badge_label.setStyleSheet(f"""
                padding: 4px 12px;
                background-color: {ThemeManager.get_color('bg_surface')};
                color: {ThemeManager.get_color('text_muted')};
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
            """)

        # Tracks table
        self._populate_tracks_table(vm.tracks)

        # Timestamp editor (only update if user hasn't manually edited)
        if vm.timestamps and not self.timestamp_editor.hasFocus():
            self.timestamp_editor.setPlainText(vm.timestamps)

    def _on_analysis_completed(self):
        """Called when analysis finishes successfully."""
        self.process_button.setEnabled(True)

    def _on_analysis_failed(self, error: str):
        """Called when analysis fails."""
        self.error_label.setText(f"Analysis Failed: {error}")
        self.error_label.show()
        self.process_button.setEnabled(False)

    # --- UI Event Handlers ---

    def _on_back_clicked(self):
        """Navigate back to Results screen."""
        self.navigate_requested.emit("RESULTS", {})

    def _on_process_clicked(self):
        """Navigate to Process screen with source and timestamp data."""
        vm: CompilationInspectorViewModel = self.viewmodel
        from ui.screens.process_screen import DownloadConfigDialog
        dialog = DownloadConfigDialog(vm.source, vm.timestamps, vm.metadata, self)
        dialog.config_confirmed.connect(self._on_config_confirmed)
        dialog.exec()

    def _on_config_confirmed(self, job):
        from ui.screens.download_screen import DownloadDialog
        self._download_dialog = DownloadDialog(job, parent=self.window())
        self._download_dialog.show()

    def _on_parse_clicked(self):
        """Parse manually edited timestamps from the editor."""
        text = self.timestamp_editor.toPlainText()
        self.viewmodel.update_timestamps(text)

    # --- Helper Methods ---

    def _make_detail_label(self, text: str) -> QLabel:
        """Creates a styled detail label."""
        label = QLabel(text)
        label.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-size: 13px;")
        label.setWordWrap(True)
        return label

    def _make_indicator(self, text: str, tooltip: str = "") -> QLabel:
        """Creates a confidence indicator label."""
        label = QLabel(f"○ {text}")
        label.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-size: 12px;")
        if tooltip:
            label.setToolTip(tooltip)
        return label

    def _update_indicator(self, label: QLabel, is_active: bool):
        """Updates a confidence indicator's visual state."""
        name = label.text().lstrip("●○ ")
        if is_active:
            label.setText(f"● {name}")
            label.setStyleSheet(f"color: {ThemeManager.get_color('accent')}; font-size: 12px;")
        else:
            label.setText(f"○ {name}")
            label.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-size: 12px;")

    def _update_status_badge(self, status: str):
        """Updates the status badge color and text."""
        status_styles = {
            "idle":      ("IDLE", ThemeManager.get_color("bg_surface"), ThemeManager.get_color("text_muted")),
            "fetching":  ("FETCHING...", ThemeManager.get_color("info_bg"), ThemeManager.get_color("info")),
            "analyzing": ("ANALYZING...", ThemeManager.get_color("warning_bg"), ThemeManager.get_color("warning")),
            "ready":     ("READY", ThemeManager.get_color("accent_muted"), ThemeManager.get_color("accent")),
            "failed":    ("FAILED", ThemeManager.get_color("danger_bg"), ThemeManager.get_color("danger")),
        }
        text, bg, fg = status_styles.get(status, ("IDLE", ThemeManager.get_color("bg_surface"), ThemeManager.get_color("text_muted")))
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(f"""
            padding: 4px 12px;
            background-color: {bg};
            color: {fg};
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)

    def _populate_tracks_table(self, tracks):
        """Populates the tracks list view."""
        while self.tracks_layout.count():
            item = self.tracks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tracks:
            self.tracks_scroll.hide()
            self.tracks_empty_label.show()
            return

        self.tracks_empty_label.hide()
        self.tracks_scroll.show()

        for i, track in enumerate(tracks):
            row = QFrame()
            row.setObjectName("TrackRow")
            row.setStyleSheet(f"""
                QFrame#TrackRow {{
                    background-color: {ThemeManager.get_color('accent_muted')};
                    border-radius: 8px;
                    border: 1px solid {ThemeManager.get_color('accent_border')};
                }}
                QFrame#TrackRow:hover {{
                    background-color: {ThemeManager.get_color('accent_hover')};
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(12)
            
            idx = QLabel(f"{i + 1}")
            idx.setFixedWidth(24)
            idx.setAlignment(Qt.AlignCenter)
            idx.setStyleSheet(f"color: {ThemeManager.get_color('text_muted')}; font-weight: bold; font-size: 13px;")
            
            start_str = CompilationInspectorViewModel._format_duration(int(track.start_time))
            end_str = CompilationInspectorViewModel._format_duration(int(track.end_time)) if track.end_time is not None else "—"
            time_lbl = QLabel(f"{start_str} - {end_str}")
            time_lbl.setFixedWidth(100)
            time_lbl.setStyleSheet(f"color: {ThemeManager.get_color('text_secondary')}; font-family: monospace; font-size: 12px;")
            
            title_lbl = QLabel(track.title)
            title_lbl.setStyleSheet(f"color: {ThemeManager.get_color('text_primary')}; font-weight: 600; font-size: 13px;")
            title_lbl.setWordWrap(True)
            
            row_layout.addWidget(idx)
            row_layout.addWidget(time_lbl)
            row_layout.addWidget(title_lbl, 1)
            
            self.tracks_layout.addWidget(row)

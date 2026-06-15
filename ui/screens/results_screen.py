from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QScrollArea, QLineEdit, QComboBox, QFrame,
    QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from ui.screens.base_screen import BaseScreen
from ui.viewmodels.results_vm import ResultsViewModel
from ui.widgets.result_card import ResultCard
from ui.widgets.filter_chip_group import FilterChipGroup
from ui.themes.theme_manager import ThemeManager


class ResultsScreen(BaseScreen):
    """
    Search Results screen  — fully responsive, premium layout.

    Vertical sections (top → bottom):
      1. Header          36px bold title + accent-keyword subtitle + Ubah Pencarian btn
      2. Filter bar      🔍 text input (stretch=1) + fixed sort dropdown
      3. Type chips      Semua / Playlist / Kompilasi  (pill buttons)
      4. Scroll area     ResultCards (10px gap, transparent scrollbar)
      5. Footer          AI note + Excellent / Great / Poor stats
    """

    # Minimum width computed from card column budgets:
    #   margin(24) + thumb(160) + sp(12) + info_min(120) + sp(12)
    #   + score(72) + sp(12) + actions(112) + margin(24) + scrollbar(8) ≈ 556
    # Use 700 to leave breathing room for the filter bar.
    SCREEN_MIN_W = 700

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_query = ""
        self._type_filter = FilterChipGroup.FILTER_ALL
        self.bind_viewmodel(ResultsViewModel())

    # ══════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        self.setMinimumWidth(self.SCREEN_MIN_W)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 20, 24, 16)
        self._layout.setSpacing(0)

        self._build_header()
        self._build_filter_bar()
        self._build_type_chips()
        self._build_scroll_area()
        self._build_footer()

    # ── 1. Header ─────────────────────────────────────────────────────

    def _build_header(self):
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 16)
        header.setSpacing(12)

        # Left: title + subtitle
        left = QVBoxLayout()
        left.setSpacing(4)

        self.title_label = QLabel("🎵 Hasil Pencarian")
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {ThemeManager.get_color('text_primary')};
        """)

        self.subtitle_label = QLabel("0 hasil ditemukan")
        self.subtitle_label.setStyleSheet(f"""
            font-size: 14px;
            color: {ThemeManager.get_color('text_secondary')};
        """)

        left.addWidget(self.title_label)
        left.addWidget(self.subtitle_label)

        header.addLayout(left)
        header.addStretch()

        # Right: Ubah Pencarian pill button
        btn_back = QPushButton("✏  Ubah Pencarian")
        btn_back.setCursor(QCursor(Qt.PointingHandCursor))
        btn_back.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeManager.get_color('accent')};
                border: 1px solid {ThemeManager.get_color('accent_border')};
                border-radius: 17px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_color('accent_muted')};
            }}
        """)
        btn_back.clicked.connect(self._on_back_to_home)
        header.addWidget(btn_back, 0, Qt.AlignVCenter)

        self._layout.addLayout(header)

    # ── 2. Filter Bar ─────────────────────────────────────────────────

    def _build_filter_bar(self):
        toolbar = QFrame()
        toolbar.setFixedHeight(44)
        toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_color('bg_card')};
                border-radius: 12px;
                border: 1px solid {ThemeManager.get_color('border')};
            }}
        """)

        row = QHBoxLayout(toolbar)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(10)

        # Search icon
        icon = QLabel("🔍")
        icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        icon.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        row.addWidget(icon)

        # Filter input — consumes all remaining space
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter hasil...")
        self.filter_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.filter_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {ThemeManager.get_color('text_primary')};
                font-size: 13px;
                padding: 0;
            }}
            QLineEdit::placeholder {{
                color: {ThemeManager.get_color('text_muted')};
            }}
        """)
        row.addWidget(self.filter_input, 1)   # stretch = 1

        # Divider
        div = QFrame()
        div.setFixedSize(1, 22)
        div.setStyleSheet(f"background: {ThemeManager.get_color('border')}; border: none;")
        row.addWidget(div)

        # "Urutkan:" label
        sort_lbl = QLabel("Urutkan:")
        sort_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sort_lbl.setStyleSheet(f"""
            font-size: 12px;
            color: {ThemeManager.get_color('text_secondary')};
            background: transparent;
            border: none;
        """)
        row.addWidget(sort_lbl)

        # Sort dropdown — fixed width, no stretch
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevansi", "Durasi", "Tanggal"])
        self.sort_combo.setCursor(Qt.PointingHandCursor)
        self.sort_combo.setFixedWidth(130)
        self.sort_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.sort_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeManager.get_color('bg_surface')};
                border: 1px solid {ThemeManager.get_color('border')};
                border-radius: 9px;
                color: {ThemeManager.get_color('text_primary')};
                font-weight: bold;
                font-size: 12px;
                padding: 3px 10px;
            }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox::down-arrow {{ image: none; border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {ThemeManager.get_color('bg_card')};
                color: {ThemeManager.get_color('text_primary')};
                border: 1px solid {ThemeManager.get_color('border')};
                border-radius: 8px;
                selection-background-color: {ThemeManager.get_color('accent_muted')};
                selection-color: {ThemeManager.get_color('text_primary')};
                padding: 4px;
            }}
        """)
        row.addWidget(self.sort_combo)

        self._layout.addWidget(toolbar)
        self._layout.addSpacing(12)

    # ── 3. Type Chips ─────────────────────────────────────────────────

    def _build_type_chips(self):
        self.chip_group = FilterChipGroup()
        self.chip_group.filter_changed.connect(self._on_type_filter_changed)
        self.chip_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._layout.addWidget(self.chip_group)
        self._layout.addSpacing(12)

    # ── 4. Scroll Area ────────────────────────────────────────────────

    def _build_scroll_area(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 5px;
                margin: 2px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {ThemeManager.get_color('border_hover')};
                border-radius: 2px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ThemeManager.get_color('text_muted')};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
                background: transparent;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)

        self.results_content = QWidget()
        self.results_content.setStyleSheet("background: transparent;")
        self.results_content_layout = QVBoxLayout(self.results_content)
        self.results_content_layout.setAlignment(Qt.AlignTop)
        self.results_content_layout.setSpacing(10)    # 10px gap between cards
        self.results_content_layout.setContentsMargins(0, 0, 6, 0)

        self.scroll_area.setWidget(self.results_content)
        self._layout.addWidget(self.scroll_area, 1)

    # ── 5. Footer ─────────────────────────────────────────────────────

    def _build_footer(self):
        self._layout.addSpacing(10)

        footer = QFrame()
        footer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_color('bg_surface')};
                border-radius: 10px;
                border: 1px solid {ThemeManager.get_color('border')};
            }}
        """)

        row = QHBoxLayout(footer)
        row.setContentsMargins(14, 8, 14, 8)
        row.setSpacing(0)

        # Left: AI note + stats stacked
        left_v = QVBoxLayout()
        left_v.setSpacing(3)
        left_v.setContentsMargins(0, 0, 0, 0)

        ai_note = QLabel(
            "AI menilai kualitas berdasarkan metadata, jumlah track, relevansi, dan konsistensi."
        )
        ai_note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ai_note.setStyleSheet(f"""
            font-size: 10px;
            color: {ThemeManager.get_color('text_muted')};
            font-style: italic;
            background: transparent;
            border: none;
        """)
        left_v.addWidget(ai_note)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        stats_row.setContentsMargins(0, 0, 0, 0)

        def stat(dot_color: str, label_text: str):
            dot = QLabel("●")
            dot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            dot.setStyleSheet(
                f"color: {dot_color}; font-size: 8px; background: transparent; border: none;"
            )
            lbl = QLabel(label_text)
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            lbl.setStyleSheet(f"""
                font-size: 11px;
                font-weight: 600;
                color: {ThemeManager.get_color('text_secondary')};
                background: transparent;
                border: none;
            """)
            h = QHBoxLayout()
            h.setSpacing(5)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(dot)
            h.addWidget(lbl)
            w = QWidget()
            w.setLayout(h)
            w.setStyleSheet("background: transparent;")
            return w, lbl

        self.w_excellent, self.lbl_excellent = stat(
            ThemeManager.get_color("success"), "Excellent 0"
        )
        self.w_great, self.lbl_great = stat(
            ThemeManager.get_color("warning"), "Great 0"
        )
        self.w_poor, self.lbl_poor = stat(
            ThemeManager.get_color("danger"), "Poor 0"
        )

        stats_row.addWidget(self.w_excellent)
        stats_row.addWidget(self.w_great)
        stats_row.addWidget(self.w_poor)
        stats_row.addStretch()

        left_v.addLayout(stats_row)
        row.addLayout(left_v, 1)

        # Right: total
        self.lbl_total = QLabel("Total 0 hasil")
        self.lbl_total.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_total.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {ThemeManager.get_color('text_primary')};
            background: transparent;
            border: none;
        """)
        row.addWidget(self.lbl_total, 0, Qt.AlignVCenter | Qt.AlignRight)

        self._layout.addWidget(footer)

    # ══════════════════════════════════════════════════════════════════
    # SIGNALS / VIEWMODEL
    # ══════════════════════════════════════════════════════════════════

    def connect_signals(self):
        vm: ResultsViewModel = self.viewmodel
        vm.results_loaded.connect(self._on_results_loaded)
        vm.source_selected.connect(self._on_source_selected)
        vm.filter_applied.connect(self._refresh_ui)
        vm.sort_applied.connect(self._refresh_ui)

        self.filter_input.textChanged.connect(vm.apply_filter)
        self.sort_combo.currentTextChanged.connect(vm.apply_sort)

    def on_navigated(self, **kwargs):
        self.current_query = kwargs.get("query", "")
        payload = kwargs.get("results")
        if payload:
            self.viewmodel.load_results(payload)

    # ══════════════════════════════════════════════════════════════════
    # SLOTS
    # ══════════════════════════════════════════════════════════════════

    def _on_results_loaded(self):
        from ui.debug_reporter import DebugSearchReporter
        reporter = DebugSearchReporter()
        vm: ResultsViewModel = self.viewmodel
        total_received = sum(len(g.sources) for g in vm.playlists) + sum(len(g.sources) for g in vm.compilations)
        reporter.signal_received = total_received
        self._refresh_ui()

    def _on_type_filter_changed(self, key: str):
        self._type_filter = key
        self._refresh_ui()

    def _on_back_to_home(self):
        self.navigate_requested.emit("HOME", {})

    def _on_source_selected(self, source):
        self.navigate_requested.emit("INSPECTOR", {"source": source})

    # ══════════════════════════════════════════════════════════════════
    # REFRESH / RENDER
    # ══════════════════════════════════════════════════════════════════

    def _refresh_ui(self):
        self._clear(self.results_content_layout)

        vm: ResultsViewModel = self.viewmodel
        
        from ui.debug_reporter import DebugSearchReporter
        reporter = DebugSearchReporter()
        reporter.selected_tab = self._type_filter
        reporter.selected_sort = vm.active_sort
        reporter.search_query = self.current_query

        # Build flat list  (source, quality, type_str)
        all_items: list[tuple] = []
        for g in vm.playlists:
            for s in g.sources:
                all_items.append((s, g.quality_results.get(s.id), "playlist"))
        for g in vm.compilations:
            for s in g.sources:
                all_items.append((s, g.quality_results.get(s.id), "compilation"))

        # Type-chip filter
        if self._type_filter == FilterChipGroup.FILTER_PLAYLIST:
            all_items = [(s, q, t) for s, q, t in all_items if t == "playlist"]
        elif self._type_filter == FilterChipGroup.FILTER_COMPILATION:
            all_items = [(s, q, t) for s, q, t in all_items if t == "compilation"]
            
        reporter.after_tab_filter = len(all_items)

        # Text filter
        term = vm.active_filter.lower()
        if term:
            all_items = [
                (s, q, t) for s, q, t in all_items
                if term in s.title.lower() or term in s.channel.lower()
            ]
            
        reporter.after_filter = len(all_items)

        # Sort
        if vm.active_sort == "Durasi":
            all_items.sort(key=lambda x: getattr(x[0], 'duration', 0) or 0, reverse=True)
        elif vm.active_sort == "Tanggal":
            all_items.sort(
                key=lambda x: x[0].upload_date or "",
                reverse=True,
            )

        # Chip counts (always from full unfiltered data)
        n_pl   = sum(len(g.sources) for g in vm.playlists)
        n_comp = sum(len(g.sources) for g in vm.compilations)
        self.chip_group.update_counts(n_pl + n_comp, n_pl, n_comp)

        # Header subtitle with accent keyword
        kw_html = (
            f'<span style="color:{ThemeManager.get_color("accent")}">"{self.current_query}"</span>'
            if self.current_query else ""
        )
        self.subtitle_label.setText(
            f"Ditemukan {len(all_items)} hasil"
            + (f" untuk {kw_html}" if kw_html else "")
        )
        self.subtitle_label.setTextFormat(Qt.RichText)

        # Empty state
        if not all_items:
            if self._type_filter == FilterChipGroup.FILTER_PLAYLIST and getattr(vm, 'playlist_failed', False):
                self._show_empty("Playlist search failed")
            else:
                self._show_empty("Tidak ada hasil ditemukan.")
            self._update_stats([])
            reporter.cards_created = 0
            reporter.cards_added_to_layout = 0
            reporter.visible_cards = 0
            reporter.write_report()
            return

        reporter.cards_created = len(all_items)
        cards_added = 0

        # Render cards
        for source, quality, type_str in all_items:
            card = ResultCard(source, quality, source_type=type_str)
            card.clicked.connect(self.viewmodel.select_source)
            card.select_requested.connect(self.viewmodel.select_source)
            self.results_content_layout.addWidget(card)
            cards_added += 1

        reporter.cards_added_to_layout = cards_added
        reporter.visible_cards = cards_added
        reporter.write_report()
        self._update_stats(all_items)

    def _update_stats(self, items):
        excellent = great = poor = 0
        for _, q, _ in items:
            s = q.score if q else 0
            if s >= 95:
                excellent += 1
            elif s >= 80:
                great += 1
            else:
                poor += 1
        self.lbl_excellent.setText(f"Excellent {excellent}")
        self.lbl_great.setText(f"Great {great}")
        self.lbl_poor.setText(f"Poor {poor}")
        self.lbl_total.setText(f"Total {len(items)} hasil")

    def _show_empty(self, msg: str):
        lbl = QLabel(msg)
        lbl.setStyleSheet(f"""
            color: {ThemeManager.get_color('text_muted')};
            font-style: italic;
            font-size: 15px;
            padding: 40px;
        """)
        lbl.setAlignment(Qt.AlignCenter)
        self.results_content_layout.addWidget(lbl)
        self.results_content_layout.addStretch()

    @staticmethod
    def _clear(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                ResultsScreen._clear(item.layout())

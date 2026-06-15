from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QVariantAnimation
from PySide6.QtGui import QColor, QCursor
from ui.themes.theme_manager import ThemeManager


class FilterChip(QPushButton):
    """
    A single pill-shaped filter chip with smooth hover/active transitions.
    Height ~36 px, full radius (pill), animated.
    """

    def __init__(self, label: str, count: int = 0, parent=None):
        super().__init__(parent)
        self._label = label
        self._count = count
        self._is_active = False
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(36)
        self.setCheckable(True)
        self._update_text()
        self._apply_style()
        self.installEventFilter(self)

        # Animation for smooth border/bg transition
        self._bg_anim = QVariantAnimation(self)
        self._bg_anim.setDuration(180)
        self._bg_anim.valueChanged.connect(self._on_anim_tick)

    def _update_text(self):
        if self._count > 0:
            self.setText(f"  {self._label} ({self._count})  ")
        else:
            self.setText(f"  {self._label}  ")

    def set_count(self, count: int):
        self._count = count
        self._update_text()

    def set_active(self, active: bool):
        self._is_active = active
        self.setChecked(active)
        self._apply_style()

    def _apply_style(self):
        if self._is_active:
            bg = ThemeManager.get_color("accent")
            fg = "#ffffff"
            border = ThemeManager.get_color("accent")
        else:
            bg = ThemeManager.get_color("bg_card")
            fg = ThemeManager.get_color("text_secondary")
            border = ThemeManager.get_color("border")

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 18px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)

    def _on_anim_tick(self, val):
        bg_c, fg_c, br_c = val
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_c.name()};
                color: {fg_c.name()};
                border: 1px solid {br_c.name()};
                border-radius: 18px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)

    def eventFilter(self, obj, event):
        if obj == self and not self._is_active:
            if event.type() == event.Type.Enter:
                hover_bg = ThemeManager.get_color("bg_hover")
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {hover_bg};
                        color: {ThemeManager.get_color('text_primary')};
                        border: 1px solid {ThemeManager.get_color('border_hover')};
                        border-radius: 18px;
                        padding: 0 18px;
                        font-size: 13px;
                        font-weight: 600;
                    }}
                """)
            elif event.type() == event.Type.Leave:
                self._apply_style()
        return super().eventFilter(obj, event)


class FilterChipGroup(QWidget):
    """
    A horizontal row of mutually exclusive filter chips.
    Emits `filter_changed(str)` when the active chip changes.
    """
    filter_changed = Signal(str)

    FILTER_ALL = "Semua"
    FILTER_PLAYLIST = "Playlist"
    FILTER_COMPILATION = "Kompilasi"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._chips: dict[str, FilterChip] = {}
        self._active_key = self.FILTER_ALL

        for key in [self.FILTER_ALL, self.FILTER_PLAYLIST, self.FILTER_COMPILATION]:
            chip = FilterChip(key)
            chip.clicked.connect(lambda checked, k=key: self._on_chip_clicked(k))
            self._chips[key] = chip
            layout.addWidget(chip)

        layout.addStretch()

        # Default: "Semua" active
        self._chips[self.FILTER_ALL].set_active(True)

    def update_counts(self, total: int, playlist_count: int, compilation_count: int):
        self._chips[self.FILTER_ALL].set_count(total)
        self._chips[self.FILTER_PLAYLIST].set_count(playlist_count)
        self._chips[self.FILTER_COMPILATION].set_count(compilation_count)

    def _on_chip_clicked(self, key: str):
        if key == self._active_key:
            return
        self._active_key = key
        for k, chip in self._chips.items():
            chip.set_active(k == key)
        self.filter_changed.emit(key)

    @property
    def active_filter(self) -> str:
        return self._active_key

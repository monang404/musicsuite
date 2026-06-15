from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import (
    QCursor, QPixmap, QPainter, QPainterPath, QColor, QFont,
    QBrush, QPen, QLinearGradient
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl

from engines.search.models.search_entity import SearchEntity
from engines.search.models.quality_result import QualityResult
from ui.themes.theme_manager import ThemeManager
from ui.widgets.circular_progress import CircularProgress


# ─────────────────────────────────────────────────────────────────────────────
# Thumbnail  (Column 1)
# Fixed 160×90, never grows, never shrinks.
# ─────────────────────────────────────────────────────────────────────────────

class ThumbnailWidget(QLabel):
    """Fixed 160×90 px thumbnail. Size is permanently locked."""

    W, H = 160, 90

    def __init__(self, url: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(self.W, self.H)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {ThemeManager.get_color('bg_surface')};
                border-radius: 12px;
                border: 1px solid {ThemeManager.get_color('border')};
            }}
        """)
        self._placeholder()
        if url:
            self._load(url)

    def _placeholder(self):
        pix = QPixmap(self.W, self.H)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.W, self.H)
        grad.setColorAt(0.0, QColor(ThemeManager.get_color("bg_card")))
        grad.setColorAt(1.0, QColor(ThemeManager.get_color("bg_surface")))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.W, self.H, 12, 12)
        p.fillPath(path, QBrush(grad))
        p.setPen(QPen(QColor(ThemeManager.get_color("text_muted"))))
        f = QFont()
        f.setPixelSize(26)
        p.setFont(f)
        p.drawText(pix.rect(), Qt.AlignCenter, "🎵")
        p.end()
        self._round(pix)

    _pixmap_cache = {}

    def _load(self, url: str):
        if url in self._pixmap_cache:
            self.setPixmap(self._pixmap_cache[url])
            return
            
        self._url = url
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._done)
        self._nam.get(QNetworkRequest(QUrl(url)))

    def _done(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NoError:
            pix = QPixmap()
            if pix.loadFromData(reply.readAll()):
                sc = pix.scaled(self.W, self.H,
                                Qt.KeepAspectRatioByExpanding,
                                Qt.SmoothTransformation)
                x = (sc.width() - self.W) // 2
                y = (sc.height() - self.H) // 2
                out = self._round_pixmap(sc.copy(max(0, x), max(0, y), self.W, self.H))
                self.setPixmap(out)
                self._pixmap_cache[self._url] = out
        reply.deleteLater()

    def _round_pixmap(self, pix: QPixmap) -> QPixmap:
        out = QPixmap(pix.size())
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pix.width(), pix.height(), 12, 12)
        p.setClipPath(path)
        p.drawPixmap(0, 0, pix)
        p.end()
        return out

    def _round(self, pix: QPixmap):
        self.setPixmap(self._round_pixmap(pix))


# ─────────────────────────────────────────────────────────────────────────────
# Info Column  (Column 2 — stretchy)
# Title + badge + metadata + 1-line description.
# Takes ALL remaining horizontal space.
# ─────────────────────────────────────────────────────────────────────────────

class _InfoColumn(QWidget):
    """
    Stretchy info column.
    Width = total card width minus thumbnail(160) minus score(72) minus actions(116) minus spacings.
    Uses Expanding horizontal policy so the card determines its final width.
    """

    def __init__(self, source: SearchEntity, source_type: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(120)   # hard floor — never collapses below this

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        # ── Title row (title + badge) ─────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(source.title)
        title_lbl.setWordWrap(True)
        title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Two lines at ~22px line-height = 44px max
        title_lbl.setMaximumHeight(46)
        title_lbl.setStyleSheet(f"""
            font-size: 15px;
            font-weight: bold;
            color: {ThemeManager.get_color('text_primary')};
            line-height: 1.4;
        """)
        title_row.addWidget(title_lbl, 1)

        # Badge (fixed, after title)
        # Badge (fixed, after title)
        if source_type == "compilation":
            badge_txt = "KOMPILASI"
            badge_bg = ThemeManager.get_color("badge_compilation_bg")
            badge_fg = ThemeManager.get_color("badge_compilation_fg")
        else:
            badge_txt = "PLAYLIST"
            badge_bg = ThemeManager.get_color("badge_playlist_bg")
            badge_fg = ThemeManager.get_color("badge_playlist_fg")

        badge = QLabel(badge_txt)
        badge.setAlignment(Qt.AlignCenter)
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        badge.setFixedHeight(18)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_bg};
                color: {badge_fg};
                font-size: 9px;
                font-weight: bold;
                padding: 1px 8px;
                border-radius: 9px;
                letter-spacing: 0.8px;
            }}
        """)
        title_row.addWidget(badge, 0, Qt.AlignTop | Qt.AlignRight)

        vbox.addLayout(title_row)

        # ── Metadata row ──────────────────────────────────────────────
        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        meta_row.setContentsMargins(0, 0, 0, 0)

        def m(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            lbl.setStyleSheet(
                f"font-size: 11px; color: {ThemeManager.get_color('text_secondary')};"
            )
            return lbl

        dur = getattr(source, 'duration', 0)
        if isinstance(dur, int) and dur > 0:
            mm, ss = divmod(dur, 60)
            hh, mm = divmod(mm, 60)
            dur_str = f"{hh}h {mm}m" if hh > 0 else f"{mm}m"
        else:
            dur_str = "—"

        type_icon = "📦" if source_type == "compilation" else "🎵"
        type_name = "Album" if source_type == "compilation" else "Playlist"

        meta_row.addWidget(m(f"👤 {source.channel}"))
        meta_row.addWidget(m(f"🕒 {dur_str}"))
        track_count = getattr(source, 'track_count', getattr(source, 'item_count', 0))
        if track_count > 0:
            meta_row.addWidget(m(f"🎵 {track_count} track"))
        meta_row.addWidget(m(f"{type_icon} {type_name}"))
        
        # Tahun upload
        upload_date = getattr(source, 'upload_date', '') or ''
        if upload_date and len(upload_date) >= 4:
            year = upload_date[:4]
            meta_row.addWidget(m(f"📅 {year}"))

        # View count (compilation only)
        if source_type == "compilation":
            views = getattr(source, 'view_count', 0) or 0
            if views > 0:
                views_str = f"{views/1_000_000:.1f}M" if views >= 1_000_000 else f"{views//1_000}K"
                meta_row.addWidget(m(f"👁 {views_str}"))

        meta_row.addStretch()   # push everything left, prevent rightward overflow

        vbox.addLayout(meta_row)

        # ── Description (1 line) ──────────────────────────────────────
        desc = QLabel(self._describe(source, source_type))
        desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        desc.setMaximumHeight(18)   # 1 line only
        desc.setStyleSheet(f"""
            font-size: 11px;
            color: {ThemeManager.get_color('text_muted')};
        """)
        vbox.addWidget(desc)

    @staticmethod
    def _describe(src: SearchEntity, kind: str) -> str:
        ch = src.channel or "Unknown"
        t  = getattr(src, 'track_count', getattr(src, 'item_count', 0))
        if t > 0:
            return f"{ch}  ·  {t} lagu pilihan"
        d = getattr(src, 'duration', 0)
        if isinstance(d, int) and d > 0:
            return f"{ch}  ·  {d // 60} menit"
        return ch


# ─────────────────────────────────────────────────────────────────────────────
# Score Column  (Column 3 — fixed width)
# Circular confidence indicator. Width = size of CircularProgress widget.
# ─────────────────────────────────────────────────────────────────────────────

class _ScoreColumn(QWidget):
    """Thin fixed-width column housing only the circular progress indicator."""

    CIRC_SIZE = 60   # diameter in px
    COL_W     = 72   # column width = circ + a little breathing room

    def __init__(self, quality: QualityResult, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.COL_W)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        score_val = quality.score if quality else 0
        circ = CircularProgress(score_val, size=self.CIRC_SIZE)
        circ.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        vbox.addWidget(circ, 0, Qt.AlignHCenter | Qt.AlignVCenter)

        is_estimate = getattr(quality, 'is_estimate', False) if quality else False
        if is_estimate:
            est_lbl = QLabel("estimasi")
            est_lbl.setAlignment(Qt.AlignCenter)
            est_lbl.setStyleSheet(f"""
                font-size: 8px;
                color: {ThemeManager.get_color('text_muted')};
                font-style: italic;
            """)
            vbox.addWidget(est_lbl, 0, Qt.AlignHCenter)


# ─────────────────────────────────────────────────────────────────────────────
# Actions Column  (Column 4 — fixed width)
# Three vertically stacked buttons.
# ─────────────────────────────────────────────────────────────────────────────

class _ActionsColumn(QWidget):
    """
    Fixed-width actions column.
    Contains single primary action.
    """

    COL_W = 112  # fixed column width

    def __init__(self, source: SearchEntity, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.COL_W)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(6)
        vbox.setAlignment(Qt.AlignVCenter)

        self._btn_detail = self._make_btn("Lihat Detail", primary=True)

        vbox.addWidget(self._btn_detail)

    @property
    def btn_detail(self) -> QPushButton:  return self._btn_detail

    def _make_btn(self, text: str, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        # Full width of the column, consistent fixed height
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFixedHeight(28)
        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.get_color('accent')};
                    color: #ffffff;
                    border: none;
                    border-radius: 7px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.get_color('accent_hover')};
                }}
                QPushButton:disabled {{
                    background-color: {ThemeManager.get_color('bg_hover')};
                    color: {ThemeManager.get_color('text_muted')};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ThemeManager.get_color('text_primary')};
                    border: 1px solid {ThemeManager.get_color('border')};
                    border-radius: 7px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.get_color('bg_hover')};
                    border: 1px solid {ThemeManager.get_color('border_hover')};
                }}
                QPushButton:disabled {{
                    color: {ThemeManager.get_color('text_muted')};
                    border-color: {ThemeManager.get_color('border')};
                }}
            """)
        return btn


# ─────────────────────────────────────────────────────────────────────────────
# ResultCard
# ─────────────────────────────────────────────────────────────────────────────

class ResultCard(QFrame):
    """
    Fully responsive, compact search-result card.

    4-column QHBoxLayout:
      Col 1 — ThumbnailWidget   [fixed 160×90, stretch=0]
      Col 2 — _InfoColumn       [stretch=1,    min=120]
      Col 3 — _ScoreColumn      [fixed 72px,   stretch=0]
      Col 4 — _ActionsColumn    [fixed 112px,  stretch=0]

    Target card height: ~120–135 px.
    Only the info column grows/shrinks with the window.
    No overlapping is possible because the three fixed columns always claim
    their declared pixel budgets first.
    """

    clicked           = Signal(object)
    select_requested  = Signal(object)

    def __init__(
        self,
        source: SearchEntity,
        quality: QualityResult = None,
        source_type: str = "playlist",
        parent=None,
    ):
        super().__init__(parent)
        self.source      = source
        self.quality     = quality
        self.source_type = source_type
        self._shadow: QGraphicsDropShadowEffect | None = None
        self._build()

    def _build(self):
        self.setObjectName("ResultCardV2")
        self._style_normal()
        # Card grows horizontally, wraps its content vertically
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(6)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(QColor(0, 0, 0, 35))
        self.setGraphicsEffect(self._shadow)

        # ── 4-column row ───────────────────────────────────────────────
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        # Col 1 — thumbnail (fixed, top-aligned)
        thumb = ThumbnailWidget(self.source.thumbnail_url)
        row.addWidget(thumb, 0, Qt.AlignTop | Qt.AlignLeft)

        # Col 2 — info (stretchy, top-aligned)
        info = _InfoColumn(self.source, self.source_type)
        row.addWidget(info, 1)          # stretch = 1

        # Col 3 — score (fixed, centered)
        score = _ScoreColumn(self.quality)
        row.addWidget(score, 0, Qt.AlignVCenter)

        # Col 4 — actions (fixed, centered)
        actions = _ActionsColumn(self.source)
        actions.btn_detail.clicked.connect(
            lambda: self.select_requested.emit(self.source))
        row.addWidget(actions, 0, Qt.AlignVCenter)

    # ── style helpers ───────────────────────────────────────────────────

    def _style_normal(self):
        self.setStyleSheet(f"""
            #ResultCardV2 {{
                background-color: {ThemeManager.get_color('bg_card')};
                border: 1px solid {ThemeManager.get_color('border')};
                border-radius: 18px;
            }}
        """)

    def _style_hover(self):
        self.setStyleSheet(f"""
            #ResultCardV2 {{
                background-color: {ThemeManager.get_color('bg_hover')};
                border: 1px solid {ThemeManager.get_color('border_hover')};
                border-radius: 18px;
            }}
        """)

    # ── hover ───────────────────────────────────────────────────────────

    def enterEvent(self, event):
        super().enterEvent(event)
        self._style_hover()
        if self._shadow:
            self._shadow.setBlurRadius(18)
            self._shadow.setOffset(0, 4)
            self._shadow.setColor(QColor(0, 0, 0, 60))

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._style_normal()
        if self._shadow:
            self._shadow.setBlurRadius(6)
            self._shadow.setOffset(0, 2)
            self._shadow.setColor(QColor(0, 0, 0, 35))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.source)

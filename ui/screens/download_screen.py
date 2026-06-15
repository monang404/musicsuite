import os
import re
import logging
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QWidget, QFrame, QDialog, QProgressBar
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from ui.viewmodels.queue_vm import QueueViewModel
from ui.viewmodels.process_vm import WorkflowJob
from ui.themes.theme_manager import ThemeManager
from ui.widgets.thinking_orb import ThinkingOrb

class StagePill(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.set_active(False)

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                background: {ThemeManager.get_color('accent_muted')};
                color: {ThemeManager.get_color('accent')};
                border: 1px solid {ThemeManager.get_color('accent_border')};
                border-radius: 10px; padding: 2px 10px; font-size: 11px;
            """)
        else:
            self.setStyleSheet(f"""
                background: transparent;
                color: {ThemeManager.get_color('text_muted')};
                border-radius: 10px; padding: 2px 10px; font-size: 11px;
            """)

class DownloadDialog(QDialog):
    """
    Floating always-on-top dialog untuk monitoring download.
    Mirip IDM: kecil, informatif, tidak menghalangi app.
    """
    def __init__(self, job: WorkflowJob, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mengunduh...")
        self.setFixedSize(420, 280)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        self.current_job_id = None
        self.current_output_folder = job.output_folder
        self.job = job
        
        self.viewmodel = QueueViewModel()
        
        self._setup_ui()
        self.connect_signals()
        
        # Add fade-in animation
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._fade_anim_slot = None
        self._fade_anim.start()
        
        # Initial State Setup
        self.title_label.setText(self.job.source.title if self.job.source else "Unknown Title")
        track_count = 1
        if self.job.source and getattr(self.job.source, "entity_type", "compilation") == "playlist":
            track_count = len(getattr(self.job.source, "entries", []))
        elif self.job.source and hasattr(self.job.source, "timestamps") and self.job.source.timestamps:
            track_count = len(self.job.source.timestamps)
            if track_count == 0: track_count = 1
        
        entity_type = "Compilation"
        self.is_playlist = False
        if self.job.source:
            entity_str = getattr(self.job.source, "entity_type", "compilation")
            self.is_playlist = entity_str == "playlist"
            entity_type = entity_str.capitalize()
            
        self.subtitle_label.setText(f"{entity_type} • {track_count} tracks")

        # Start job
        self.viewmodel.add_workflow_job(self.job)
        jobs = self.viewmodel._queue_service.get_all_jobs()
        if jobs:
            self.current_job_id = jobs[-1].id

        self._show_downloading_state()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        from ui.widgets.title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, title="Download", show_minimize=False, show_maximize=False)
        main_layout.addWidget(self.title_bar)
        
        content_widget = QWidget()
        main_layout.addWidget(content_widget)
        
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)
        
        bg_card = ThemeManager.get_color('bg_card')
        self.setStyleSheet(f"""
            QDialog {{ 
                background-color: {bg_card}; 
                border: 1px solid {ThemeManager.get_color('border')};
            }}
            QLabel {{ background: transparent; }}
        """)
        
        # Top: Icon & Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        self.status_icon = QLabel("♪")
        self.status_icon.setStyleSheet(f"font-size: 24px; color: {ThemeManager.get_color('accent')}; font-weight: bold;")
        self.status_icon.setFixedSize(32, 32)
        self.status_icon.setAlignment(Qt.AlignCenter)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        self.title_label = QLabel("...")
        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")
        self.title_label.setWordWrap(True)
        self.subtitle_label = QLabel("...")
        self.subtitle_label.setStyleSheet(f"font-size: 11px; color: {ThemeManager.get_color('text_secondary')};")
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        
        header_layout.addWidget(self.status_icon)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.layout.addLayout(header_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: {ThemeManager.get_color('bg_surface')};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ThemeManager.get_color('accent')},
                    stop:1 {ThemeManager.get_color('accent_light')});
            }}
        """)
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self._progress_anim.setDuration(300)
        self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.layout.addSpacing(10)
        self.layout.addWidget(self.progress_bar)
        
        # Stage label & Detail Line
        self.stage_layout = QVBoxLayout()
        self.stage_layout.setSpacing(4)
        
        stage_title_layout = QHBoxLayout()
        self.thinking_orb = ThinkingOrb()
        self.stage_label = QLabel("Menyiapkan...")
        self.stage_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ThemeManager.get_color('text_primary')};")
        self.stage_label.setWordWrap(True)
        
        stage_title_layout.addWidget(self.thinking_orb)
        stage_title_layout.addWidget(self.stage_label)
        stage_title_layout.addStretch()
        
        self.thinking_orb.start()
        
        self.stage_layout.addLayout(stage_title_layout)
        
        self.layout.addSpacing(5)
        self.layout.addLayout(self.stage_layout)
        
        # Stages Timeline
        stages_layout = QHBoxLayout()
        stages_layout.setSpacing(8)
        self.stage_pills = [
            StagePill("⬇ Unduh"),
            StagePill("⏱ Timestamp"),
            StagePill("✂ Potong"),
            StagePill("✓ Selesai")
        ]
        for pill in self.stage_pills:
            stages_layout.addWidget(pill)
        stages_layout.addStretch()
        
        self.layout.addSpacing(10)
        self.layout.addLayout(stages_layout)
        
        # Success / Fail specific labels
        self.result_info_label = QLabel("")
        self.result_info_label.setStyleSheet(f"font-size: 12px; color: {ThemeManager.get_color('text_secondary')};")
        self.result_info_label.setWordWrap(True)
        self.layout.addWidget(self.result_info_label)
        self.result_info_label.hide()
        
        # Buttons
        self.layout.addStretch()
        self.btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Batalkan Unduhan")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(self._btn_style(is_primary=False))
        
        self.open_folder_btn = QPushButton("📁 Buka Folder")
        self.open_folder_btn.setCursor(Qt.PointingHandCursor)
        self.open_folder_btn.setStyleSheet(self._btn_style(is_primary=True))
        
        self.back_btn = QPushButton("← Kembali")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(self._btn_style(is_primary=False))
        
        self.home_btn = QPushButton("🏠")
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.setStyleSheet(self._btn_style(is_primary=False))
        
        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.cancel_btn)
        self.btn_layout.addWidget(self.open_folder_btn)
        self.btn_layout.addWidget(self.back_btn)
        self.btn_layout.addWidget(self.home_btn)
        self.btn_layout.addStretch()
        
        self.layout.addLayout(self.btn_layout)

    def _btn_style(self, is_primary=False):
        bg = ThemeManager.get_color('accent') if is_primary else "transparent"
        color = ThemeManager.get_color('bg_main') if is_primary else ThemeManager.get_color('text_primary')
        border = "none" if is_primary else f"1px solid {ThemeManager.get_color('text_secondary')}"
        hover_bg = ThemeManager.get_color('accent_hover') if is_primary else ThemeManager.get_color('bg_card')
        return f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {bg};
                color: {color};
                border: {border};
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """

    def connect_signals(self):
        vm: QueueViewModel = self.viewmodel
        vm.job_started.connect(self._on_job_started)
        vm.job_progress.connect(self._on_job_progress)
        vm.job_completed.connect(self._on_job_completed)
        vm.job_failed.connect(self._on_job_failed)
        vm.job_cancelled.connect(self._on_job_cancelled)
        
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        self.back_btn.clicked.connect(self.accept)
        self.home_btn.clicked.connect(self.accept)
        
    def accept(self):
        self._fade_out_and_close(lambda: QDialog.accept(self))

    def reject(self):
        self._fade_out_and_close(lambda: QDialog.reject(self))
        
    def _fade_out_and_close(self, callback):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        if self._fade_anim_slot:
            try:
                self._fade_anim.finished.disconnect(self._fade_anim_slot)
            except Exception:
                logging.error("Failed to disconnect fade animation", exc_info=True)
        self._fade_anim_slot = callback
        self._fade_anim.finished.connect(self._fade_anim_slot)
        self._fade_anim.start()

    def _show_downloading_state(self):
        self.status_icon.setText("♪")
        self.status_icon.setStyleSheet(f"font-size: 24px; color: {ThemeManager.get_color('accent')}; font-weight: bold;")
        
        self.progress_bar.show()
        self.stage_label.show()
        self.thinking_orb.show()
        for p in self.stage_pills: p.show()
        self.result_info_label.hide()
        
        self.thinking_orb.start()
        
        self.cancel_btn.show()
        self.open_folder_btn.hide()
        self.back_btn.hide()
        self.home_btn.hide()

    def _show_completed_state(self, track_count):
        self.status_icon.setText("✓")
        self.status_icon.setStyleSheet(f"font-size: 24px; color: {ThemeManager.get_color('success')}; font-weight: bold;")
        self.title_label.setText("Unduhan Selesai")
        self.subtitle_label.setText("")
        
        self.progress_bar.hide()
        self.thinking_orb.stop()
        self.thinking_orb.hide()
        self.stage_label.hide()
        for p in self.stage_pills: p.hide()
        
        self.result_info_label.setText(f"{track_count} tracks tersimpan\n{self.current_output_folder}")
        self.result_info_label.show()
        
        self.cancel_btn.hide()
        self.open_folder_btn.show()
        self.back_btn.show()
        self.home_btn.show()

    def _show_failed_state(self, err_msg, is_cancel=False):
        self.status_icon.setText("✕")
        self.status_icon.setStyleSheet(f"font-size: 24px; color: {ThemeManager.get_color('danger')}; font-weight: bold;")
        self.title_label.setText("Unduhan Dibatalkan" if is_cancel else "Unduhan Gagal")
        self.subtitle_label.setText("")
        
        self.progress_bar.hide()
        self.thinking_orb.stop()
        self.thinking_orb.hide()
        self.stage_label.hide()
        for p in self.stage_pills: p.hide()
        
        self.result_info_label.setText(err_msg)
        self.result_info_label.show()
        
        self.cancel_btn.hide()
        self.open_folder_btn.hide()
        self.back_btn.show()
        self.home_btn.show()

    def _parse_progress(self, msg: str, pct: float) -> tuple[int, str, float, int, int]:
        """Returns (stage_index, detail_text, actual_pct, track_cur, track_total)"""
        msg_lower = msg.lower()
        actual_pct = pct
        track_cur = 1
        track_total = 1
        
        pct_match = re.search(r'(\d+(?:\.\d+)?)%', msg)
        if pct_match:
            actual_pct = float(pct_match.group(1)) / 100.0
            
        track_match = re.search(r'Track\s+(\d+)/(\d+)', msg)
        if track_match:
            track_cur, track_total = int(track_match.group(1)), int(track_match.group(2))
            
        if "fetching" in msg_lower or "download" in msg_lower or "mengunduh" in msg_lower:
            size_match = re.search(r'(?:of\s+|~)?([\d\.]+\s*(?:KiB|MiB|GiB|B|MB|KB))', msg)
            speed_match = re.search(r'(?:at\s+|⚡\s*)([\d\.]+\s*(?:KiB/s|MiB/s|GiB/s|B/s|MB/s|KB/s))', msg)
            eta_match = re.search(r'(?:ETA\s+|⏳\s*)([\d:~]+)', msg)
            
            parts = []
            if track_match:
                parts.append(f"Track {track_cur}/{track_total} •")
            parts.append("Mengunduh data")
                
            info = []
            if size_match: info.append(size_match.group(1).replace('MiB', 'MB').replace('KiB', 'KB'))
            if speed_match: info.append(f"⚡ {speed_match.group(1).replace('MiB/s', 'MB/s').replace('KiB/s', 'KB/s')}")
            if eta_match: info.append(f"⏳ {eta_match.group(1)}")
            
            if info:
                parts.append("— " + " ".join(info))
                
            return 0, " ".join(parts), actual_pct, track_cur, track_total
            
        elif "timestamp" in msg_lower or "parsing" in msg_lower or "generating" in msg_lower:
            return 1, "Menganalisis dan memproses metadata...", actual_pct, track_cur, track_total
            
        elif "splitting" in msg_lower or "split" in msg_lower or "memotong" in msg_lower:
            if track_match:
                return 2, f"Memotong audio bagian {track_cur} dari {track_total}...", actual_pct, track_cur, track_total
            return 2, "Sedang memotong audio...", actual_pct, track_cur, track_total
            
        elif "complete" in msg_lower or "selesai" in msg_lower:
            return 3, "Penyelesaian tugas...", 1.0, track_cur, track_total
            
        return 0, msg, actual_pct, track_cur, track_total

    def _set_progress_smooth(self, value: int):
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(value)
        self._progress_anim.start()

    def _on_job_started(self, job_id: str):
        pass

    def _on_job_progress(self, msg: str, pct: float):
        stage_idx, detail, actual_pct, track_cur, track_total = self._parse_progress(msg, pct)
        
        for i, pill in enumerate(self.stage_pills):
            pill.set_active(i == stage_idx)
            
        if stage_idx == 3:
            self.thinking_orb.stop()
            self.thinking_orb.hide()
        else:
            if not self.thinking_orb.isVisible():
                self.thinking_orb.start()
                self.thinking_orb.show()
                
        self.stage_label.setText(detail)
        
        if self.is_playlist:
            # Playlist progress goes evenly based on track count
            overall_pct = (track_cur - 1 + actual_pct) / track_total if track_total > 0 else actual_pct
            val = int(overall_pct * 100)
            if stage_idx == 3: val = 100
        else:
            # Compilation progress is split between downloading (25%), timestamp (25%), splitting (50%)
            if stage_idx == 0:
                val = int(actual_pct * 25)
            elif stage_idx == 1:
                val = 25 + int(actual_pct * 25)
            elif stage_idx == 2:
                val = 50 + int(actual_pct * 50)
            else:
                val = 100
            
        self._set_progress_smooth(val)

    def _on_job_completed(self, results: list):
        self._show_completed_state(len(results) if results else 0)

    def _on_job_failed(self, err: str):
        self._show_failed_state(err)

    def _on_job_cancelled(self):
        self._show_failed_state("Dibatalkan oleh pengguna.", is_cancel=True)

    def _on_cancel_clicked(self):
        if self.current_job_id:
            self.viewmodel.cancel_job(self.current_job_id)
            self.reject()

    def _on_open_folder_clicked(self):
        if self.current_output_folder and os.path.exists(self.current_output_folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_output_folder))

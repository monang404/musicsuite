from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QTextEdit, QFrame, QDialog
)
from PySide6.QtCore import Qt, Signal
from ui.viewmodels.process_vm import ProcessViewModel, WorkflowJob
from ui.themes.theme_manager import ThemeManager

class DownloadConfigDialog(QDialog):
    """
    Dialog konfigurasi sebelum download dimulai.
    Dipanggil dari inspector, bukan dari navigator.
    """
    config_confirmed = Signal(WorkflowJob)

    def __init__(self, source, timestamps, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Unduhan")
        self.setMinimumWidth(500)
        
        # Setup viewmodel
        self.viewmodel = ProcessViewModel()
        self.viewmodel.load_source(source, timestamps, metadata)
        
        self._setup_ui()
        self.connect_signals()
        
        # Initial updates
        self._sync_ui_from_vm()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        bg_main = ThemeManager.get_color('bg_main')
        bg_card = ThemeManager.get_color('bg_card')
        text_primary = ThemeManager.get_color('text_primary')
        text_secondary = ThemeManager.get_color('text_secondary')
        accent = ThemeManager.get_color('accent')
        
        bg_surface = ThemeManager.get_color('bg_surface')
        border_color = ThemeManager.get_color('border')
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_surface}; }}
            QLabel {{ color: {text_primary}; background: transparent; }}
            QCheckBox {{ color: {text_primary}; background: transparent; }}
            QLineEdit, QComboBox {{
                background-color: {bg_main};
                color: {text_primary};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 6px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {accent};
            }}
            QPushButton {{
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)

        # Add fade-in animation
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._fade_anim_slot = None
        self._fade_anim.start()

        # Header (Icon + Title)
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("♪")
        icon_lbl.setStyleSheet(f"font-size: 32px; color: {accent}; font-weight: bold;")
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_text = self.viewmodel.source.title if self.viewmodel.source else "Unknown"
        title = QLabel(title_text)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_primary};")
        
        entity_type = "Compilation"
        if self.viewmodel.source:
            entity_type = getattr(self.viewmodel.source, "entity_type", "compilation").capitalize()
            
        track_count = 1
        if self.viewmodel.source and getattr(self.viewmodel.source, "entity_type", "compilation") == "playlist":
            track_count = len(getattr(self.viewmodel.source, "entries", []))
        elif self.viewmodel.source and hasattr(self.viewmodel.source, "timestamps") and self.viewmodel.source.timestamps:
            track_count = len(self.viewmodel.source.timestamps)
            if track_count == 0: track_count = 1
            
        subtitle = QLabel(f"{entity_type} • {track_count} track(s)")
        subtitle.setStyleSheet(f"font-size: 12px; color: {text_secondary};")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        self.layout.addLayout(header_layout)
        self.layout.addSpacing(10)
        
        # Error Label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444; font-weight: bold;")
        self.error_label.hide()
        self.layout.addWidget(self.error_label)

        # Content Card
        content_card = QFrame()
        content_card.setObjectName("contentCard")
        content_card.setStyleSheet(f"""
            #contentCard {{
                background-color: {ThemeManager.get_color('bg_card')};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(15)

        # Format & Quality
        fmt_layout = QHBoxLayout()
        fmt_layout.setSpacing(10)
        fmt_label = QLabel("Format:")
        fmt_label.setFixedWidth(60)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp3", "wav", "flac", "aac"])
        self.format_combo.setFixedWidth(80)
        
        bit_label = QLabel("Bitrate:")
        bit_label.setFixedWidth(60)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["320k", "256k", "192k", "128k", "64k"])
        self.bitrate_combo.setFixedWidth(80)
        
        fmt_layout.addWidget(fmt_label)
        fmt_layout.addWidget(self.format_combo)
        fmt_layout.addSpacing(20)
        fmt_layout.addWidget(bit_label)
        fmt_layout.addWidget(self.bitrate_combo)
        fmt_layout.addStretch()
        content_layout.addLayout(fmt_layout)

        # Options
        options_layout = QHBoxLayout()
        opt_label = QLabel("Opsi:")
        opt_label.setFixedWidth(60)
        options_layout.addWidget(opt_label)
        
        self.tags_checkbox = QCheckBox("Tulis Tag Meta")
        self.thumbnail_checkbox = QCheckBox("Sematkan Thumbnail")
        self.playlist_checkbox = QCheckBox("Buat File Playlist (.m3u)")
        
        options_layout.addWidget(self.tags_checkbox)
        options_layout.addWidget(self.thumbnail_checkbox)
        options_layout.addWidget(self.playlist_checkbox)
        options_layout.addStretch()
        content_layout.addLayout(options_layout)

        self.layout.addWidget(content_card)
        


        # Preview
        self.layout.addSpacing(10)
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet(f"color: {text_secondary}; font-style: italic;")
        self.layout.addWidget(self.preview_label)

        # Buttons
        self.layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"background-color: transparent; color: {text_secondary}; border: 1px solid {text_secondary};")
        
        self.start_btn = QPushButton("▶ Mulai Unduh")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet(f"background-color: {accent}; color: {bg_main}; border: none;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.start_btn)
        self.layout.addLayout(btn_layout)

    def connect_signals(self):
        vm = self.viewmodel
        
        # UI -> VM
        self.format_combo.currentTextChanged.connect(vm.set_audio_format)
        self.bitrate_combo.currentTextChanged.connect(vm.set_bitrate)
        
        self.tags_checkbox.toggled.connect(lambda v: vm.set_export_option("write_tags", v))
        self.thumbnail_checkbox.toggled.connect(lambda v: vm.set_export_option("embed_thumbnail", v))
        self.playlist_checkbox.toggled.connect(lambda v: vm.set_export_option("create_playlist", v))

        self.cancel_btn.clicked.connect(self.reject)
        self.start_btn.clicked.connect(vm.start_job)
        
        # VM -> UI
        vm.state_changed.connect(self._sync_ui_from_vm)
        vm.error_occurred.connect(self._on_error)
        vm.job_configured.connect(self._on_job_configured)

    def _sync_ui_from_vm(self):
        vm = self.viewmodel
        if self.format_combo.currentText() != vm.audio_format:
            self.format_combo.setCurrentText(vm.audio_format)
        if self.bitrate_combo.currentText() != vm.bitrate:
            self.bitrate_combo.setCurrentText(vm.bitrate)
            
        self.tags_checkbox.setChecked(vm.export_options.get("write_tags", True))
        self.thumbnail_checkbox.setChecked(vm.export_options.get("embed_thumbnail", False))
        self.playlist_checkbox.setChecked(vm.export_options.get("create_playlist", False))
        
        if vm.audio_format in ["flac", "wav"]:
            self.bitrate_combo.setDisabled(True)
        else:
            self.bitrate_combo.setDisabled(False)
            
        self._update_preview()
        self.error_label.hide()

    def _update_preview(self):
        vm = self.viewmodel
        folder = vm.output_folder or "[Select Directory]"
        
        track_count = 1
        if vm.source and getattr(vm.source, "entity_type", "compilation") == "playlist":
            track_count = len(getattr(vm.source, "entries", []))
        elif vm.source and hasattr(vm.source, "timestamps") and vm.source.timestamps:
            track_count = len(vm.source.timestamps)
            
        if track_count == 0:
            track_count = 1

        self.preview_label.setText(f"📂 Folder Output:\n{folder}")

    def _on_error(self, err: str):
        self.error_label.setText(err)
        self.error_label.show()

    def _on_job_configured(self, job: WorkflowJob):
        self.config_confirmed.emit(job)
        self.accept()

    def accept(self):
        self._fade_out_and_close(self._do_accept)

    def _do_accept(self):
        QDialog.accept(self)

    def reject(self):
        self._fade_out_and_close(self._do_reject)
        
    def _do_reject(self):
        QDialog.reject(self)
        
    def _fade_out_and_close(self, callback):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        if self._fade_anim_slot:
            try:
                self._fade_anim.finished.disconnect(self._fade_anim_slot)
            except Exception:
                pass
        self._fade_anim_slot = callback
        self._fade_anim.finished.connect(self._fade_anim_slot)
        self._fade_anim.start()

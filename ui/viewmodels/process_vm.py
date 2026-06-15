from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.core.service_container import ServiceContainer
from engines.search.models.search_entity import SearchEntity


@dataclass
class WorkflowJob:
    source: SearchEntity
    timestamps: str
    metadata: Dict[str, Any]
    output_folder: str
    audio_format: str
    bitrate: str
    naming_pattern: str
    export_options: Dict[str, Any] = field(default_factory=dict)


class ProcessViewModel(BaseViewModel):
    """
    ViewModel for the Process Screen.
    Handles configuration logic for preparing a music processing job.
    Produces a WorkflowJob DTO upon starting.
    """
    # Signals
    job_configured = Signal(object)  # Emits WorkflowJob DTO on success

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Use ServiceContainer to satisfy architectural requirements
        container = ServiceContainer()
        self._workflow_service = container.workflow_service
        
        # Initialize State
        self._source: Optional[SearchEntity] = None
        self._timestamps: str = ""
        self._metadata: Dict[str, Any] = {}
        self._output_folder: str = ""
        self._audio_format: str = "mp3"
        self._bitrate: str = "320k"
        self._naming_pattern: str = "{index:03d} - {title}"
        self._export_options: Dict[str, bool] = {
            "split_audio": True,
            "write_tags": True,
            "embed_thumbnail": False,
            "create_playlist": False
        }

    # --- Properties ---

    @property
    def source(self) -> Optional[SearchEntity]:
        return self._source

    @property
    def timestamps(self) -> str:
        return self._timestamps

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def output_folder(self) -> str:
        return self._output_folder

    @property
    def audio_format(self) -> str:
        return self._audio_format

    @property
    def bitrate(self) -> str:
        return self._bitrate

    @property
    def naming_pattern(self) -> str:
        return self._naming_pattern

    @property
    def export_options(self) -> Dict[str, bool]:
        return self._export_options

    # --- Commands ---

    def load_source(self, source: SearchEntity, timestamps: str, metadata: Dict[str, Any]):
        """Loads the source info passed during navigation."""
        self._source = source
        self._timestamps = timestamps or ""
        self._metadata = metadata or {}
        
        # Adjust defaults for playlists
        if getattr(source, "entity_type", "compilation") == "playlist":
            self._export_options["split_audio"] = False
            
        self._output_folder = self._compute_output_folder(self._source, self._metadata)
            
        self.state_changed.emit()

    def _compute_output_folder(self, source: SearchEntity, metadata: Dict[str, Any]) -> str:
        from ui.core.app_settings import AppSettings
        import os
        import re
        
        base = AppSettings.get_default_folder()
        entity_type = getattr(source, "entity_type", "compilation")
        
        title = getattr(source, "title", "Unknown")
        # Sanitize title for filesystem
        title_safe = re.sub(r'[<>:"/\\|?*]', '_', title).strip()
        
        sub = "kompilasi" if entity_type == "compilation" else "playlist"
        return os.path.join(base, sub, title_safe)

    def set_output_folder(self, folder: str):
        if self._output_folder != folder:
            self._output_folder = folder
            self.state_changed.emit()

    def set_audio_format(self, fmt: str):
        if self._audio_format != fmt:
            self._audio_format = fmt
            self.state_changed.emit()

    def set_bitrate(self, bitrate: str):
        if self._bitrate != bitrate:
            self._bitrate = bitrate
            self.state_changed.emit()

    def set_naming_pattern(self, pattern: str):
        if self._naming_pattern != pattern:
            self._naming_pattern = pattern
            self.state_changed.emit()

    def set_export_option(self, key: str, value: bool):
        if key in self._export_options and self._export_options[key] != value:
            self._export_options[key] = value
            self.state_changed.emit()

    def validate(self) -> Tuple[bool, List[str]]:
        """Validates the current configuration."""
        errors = []
        if not self._audio_format:
            errors.append("Audio format is required.")
        if not self._bitrate:
            errors.append("Bitrate is required.")
        return len(errors) == 0, errors

    def start_job(self) -> Optional[WorkflowJob]:
        """
        Validates the configuration and generates a WorkflowJob DTO.
        Emits job_configured signal on success, or error_occurred on validation failure.
        """
        is_valid, errors = self.validate()
        if not is_valid:
            error_msg = "; ".join(errors)
            self.error_occurred.emit(error_msg)
            return None
            
        import os
        os.makedirs(self._output_folder, exist_ok=True)
            
        job = WorkflowJob(
            source=self._source,
            timestamps=self._timestamps,
            metadata=self._metadata,
            output_folder=self._output_folder,
            audio_format=self._audio_format,
            bitrate=self._bitrate,
            naming_pattern=self._naming_pattern,
            export_options=self._export_options.copy()
        )
        self.job_configured.emit(job)
        return job

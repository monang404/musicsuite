from typing import Dict, List, Optional, Any
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.core.service_container import ServiceContainer
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.track import Track
from engines.search.models.quality_result import QualityResult
from ui.workers.compilation_inspector_worker import CompilationInspectorWorker


class CompilationInspectorViewModel(BaseViewModel):
    """
    ViewModel for the Inspector Screen.
    Manages source analysis state: metadata, tracks, timestamps,
    confidence scoring, and extraction status.
    
    Orchestrates SearchService (metadata fetch) and TimestampService
    (timestamp generation) through ServiceContainer.
    """

    # Signals
    analysis_completed = Signal()
    analysis_failed = Signal(str)
    source_loaded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Services via DI
        container = ServiceContainer()
        self._search_service = container.search_service
        self._timestamp_service = container.timestamp_service

        # State
        self._source: Optional[CompilationVideo] = None
        self._metadata: Dict[str, Any] = {}
        self._tracks: List[Track] = []
        self._timestamps: str = ""
        self._confidence_score: Optional[QualityResult] = None
        self._analysis_status: str = "idle"  # idle | fetching | analyzing | ready | failed
        self._error_message: str = ""

        # Worker instance
        self._worker: Optional[CompilationInspectorWorker] = None

        # Clean up worker on destruction
        self.destroyed.connect(self.cleanup_worker)

    # --- Properties ---

    @property
    def source(self) -> Optional[CompilationVideo]:
        return self._source

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def tracks(self) -> List[Track]:
        return self._tracks

    @property
    def timestamps(self) -> str:
        return self._timestamps

    @property
    def confidence_score(self) -> Optional[QualityResult]:
        return self._confidence_score

    @property
    def analysis_status(self) -> str:
        return self._analysis_status

    @property
    def error_message(self) -> str:
        return self._error_message

    # --- Commands ---

    def load_source(self, source: CompilationVideo):
        """
        Loads a source into the inspector.
        If the source is not deep-fetched, fetches full metadata first.
        Then runs analysis to compute tracks, timestamps, and confidence.
        
        Asynchronous operation: cancels any active worker before starting.
        """
        self._source = source
        self._error_message = ""
        self.source_loaded.emit()

        # 1. Cancel and clean up existing worker if running
        self.cleanup_worker()

        # 2. Determine initial status
        initial_status = "fetching" if not source.is_deep_fetched else "analyzing"
        self._set_status(initial_status)

        # 3. Create and configure worker
        self._worker = CompilationInspectorWorker(source, parent=self)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.completed.connect(self._on_worker_completed)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.cancelled.connect(self._on_worker_cancelled)
        
        # 4. Start background thread
        self._worker.start()

    def analyze_source(self):
        """
        Re-runs analysis on the current source.
        Useful if the source was updated or timestamps were edited.
        """
        if not self._source:
            return
        self.load_source(self._source)

    def update_timestamps(self, new_text: str):
        """
        Updates the timestamp text and re-parses tracks from it.
        Format expected: MM:SS|Title (one per line).
        """
        self._timestamps = new_text
        self._parse_tracks_from_text(new_text)
        self.state_changed.emit()

    def cleanup_worker(self):
        """Safely cancels and waits for the active worker thread to finish."""
        if hasattr(self, '_worker') and self._worker:
            worker = self._worker
            self._worker = None

            # Disconnect signals to prevent receiving events during cancellation/teardown
            try:
                worker.progress.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                worker.completed.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                worker.failed.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                worker.cancelled.disconnect()
            except (RuntimeError, TypeError):
                pass

            if worker.isRunning():
                worker.cancel()
                worker.wait()  # Block until the thread is fully stopped
            worker.deleteLater()

    # --- Internal Methods / Slots ---

    def _on_worker_progress(self, message: str, percent: float):
        """Worker progress handler."""
        status = "fetching" if "fetch" in message.lower() else "analyzing"
        self._set_status(status)

    def _on_worker_completed(self, result_dto: Dict[str, Any]):
        """Worker completion handler."""
        self._source = result_dto["source"]
        self._metadata = result_dto["metadata"]
        self._tracks = result_dto["tracks"]
        self._timestamps = result_dto["timestamps"]
        self._confidence_score = result_dto["confidence_score"]

        self._set_status("ready")
        self.analysis_completed.emit()
        self.cleanup_worker()

    def _on_worker_failed(self, error_msg: str):
        """Worker failure handler."""
        self._error_message = error_msg
        self._set_status("failed")
        self.analysis_failed.emit(error_msg)
        self.cleanup_worker()

    def _on_worker_cancelled(self):
        """Worker cancellation handler."""
        self._set_status("idle")
        self.cleanup_worker()

    def _set_status(self, status: str):
        """Updates analysis status and emits state change."""
        self._analysis_status = status
        self.is_loading = status in ("fetching", "analyzing")
        self.state_changed.emit()

    def _parse_tracks_from_text(self, text: str):
        """Parses tracks from MM:SS|Title formatted text."""
        self._tracks = []
        if not text.strip():
            return

        for i, line in enumerate(text.strip().split("\n")):
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            time_str, title = parts
            try:
                seconds = self._time_to_seconds(time_str.strip())
                self._tracks.append(Track(
                    title=title.strip(),
                    start_time=float(seconds),
                    end_time=None,
                    source="manual"
                ))
            except (ValueError, IndexError):
                continue

        # Calculate end times
        for i in range(len(self._tracks) - 1):
            self._tracks[i].end_time = self._tracks[i + 1].start_time

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Formats seconds into H:MM:SS or MM:SS."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _time_to_seconds(time_str: str) -> int:
        """Parses MM:SS or H:MM:SS string to seconds."""
        parts = list(map(int, time_str.strip().split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        raise ValueError(f"Invalid time format: {time_str}")

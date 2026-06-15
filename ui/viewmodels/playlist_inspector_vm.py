import copy
from typing import Dict, List, Optional, Any, Set, Tuple
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.core.service_container import ServiceContainer
from engines.search.models.playlist_source import PlaylistSource, PlaylistEntry
from engines.search.models.quality_result import QualityResult
from ui.workers.playlist_inspector_worker import PlaylistInspectorWorker


class PlaylistInspectorViewModel(BaseViewModel):
    """
    ViewModel for the Playlist Inspector Screen.
    """

    analysis_completed = Signal()
    analysis_failed = Signal(str)
    source_loaded = Signal()
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        container = ServiceContainer()
        self._search_service = container.search_service

        self._source: Optional[PlaylistSource] = None
        self._metadata: Dict[str, Any] = {}
        self._entries: List[PlaylistEntry] = []
        self._selected_indices: Set[int] = set()
        self._filter_text: str = ""
        self._confidence_score: Optional[QualityResult] = None
        self._analysis_status: str = "idle"
        self._error_message: str = ""
        self._worker: Optional[PlaylistInspectorWorker] = None

        self.destroyed.connect(self.cleanup_worker)

    @property
    def source(self) -> Optional[PlaylistSource]:
        return self._source

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def entries(self) -> List[PlaylistEntry]:
        return self._entries

    @property
    def confidence_score(self) -> Optional[QualityResult]:
        return self._confidence_score

    @property
    def analysis_status(self) -> str:
        return self._analysis_status

    @property
    def error_message(self) -> str:
        return self._error_message

    @property
    def filter_text(self) -> str:
        return self._filter_text

    @filter_text.setter
    def filter_text(self, text: str):
        if self._filter_text != text:
            self._filter_text = text
            self.state_changed.emit()

    @property
    def selected_count(self) -> int:
        return len(self._selected_indices)

    @property
    def total_count(self) -> int:
        return len(self._entries)

    def is_entry_available(self, entry: PlaylistEntry) -> bool:
        title = (entry.title or "").strip()
        return not (title.startswith("[") and title.endswith("video]"))

    def select_all(self):
        self._selected_indices = {
            i for i, entry in enumerate(self._entries) if self.is_entry_available(entry)
        }
        self.selection_changed.emit()

    def clear_selection(self):
        self._selected_indices.clear()
        self.selection_changed.emit()

    def invert_selection(self):
        self._selected_indices = {
            i for i, entry in enumerate(self._entries)
            if self.is_entry_available(entry) and i not in self._selected_indices
        }
        self.selection_changed.emit()

    def toggle_selection(self, index: int, is_selected: bool):
        if 0 <= index < len(self._entries):
            entry = self._entries[index]
            if self.is_entry_available(entry):
                if is_selected:
                    self._selected_indices.add(index)
                else:
                    self._selected_indices.discard(index)
                self.selection_changed.emit()

    def get_filtered_entries_with_indices(self) -> List[Tuple[int, PlaylistEntry]]:
        if not self._filter_text:
            return list(enumerate(self._entries))
        
        query = self._filter_text.lower()
        res = []
        for i, entry in enumerate(self._entries):
            title = (entry.title or "").lower()
            channel = (entry.channel or "").lower()
            if query in title or query in channel:
                res.append((i, entry))
        return res

    def download_selected(self) -> Optional[Tuple[PlaylistSource, Dict[str, Any]]]:
        if not self._source or not self._selected_indices:
            return None
        
        selected_entries = [self._entries[i] for i in sorted(self._selected_indices)]
        
        cloned_source = copy.copy(self._source)
        cloned_source.entries = selected_entries
        cloned_source.item_count = len(selected_entries)
        
        cloned_metadata = self._metadata.copy()
        cloned_metadata["item_count"] = len(selected_entries)
        
        return cloned_source, cloned_metadata

    def load_source(self, source: PlaylistSource):
        self._source = source
        self._error_message = ""
        self.source_loaded.emit()

        self.cleanup_worker()

        initial_status = "fetching" if not source.is_deep_fetched else "analyzing"
        self._set_status(initial_status)

        self._worker = PlaylistInspectorWorker(source, parent=self)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.completed.connect(self._on_worker_completed)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.cancelled.connect(self._on_worker_cancelled)
        
        self._worker.start()

    def analyze_source(self):
        if not self._source:
            return
        self.load_source(self._source)

    def cleanup_worker(self):
        if hasattr(self, '_worker') and self._worker:
            worker = self._worker
            self._worker = None

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
                worker.wait()
            worker.deleteLater()

    def _on_worker_progress(self, message: str, percent: float):
        status = "fetching" if "fetch" in message.lower() else "analyzing"
        self._set_status(status)

    def _on_worker_completed(self, result_dto: Dict[str, Any]):
        self._source = result_dto["source"]
        self._metadata = result_dto["metadata"]
        self._entries = result_dto["entries"]
        self._confidence_score = result_dto["confidence_score"]

        # Default: select all available entries
        self._selected_indices = {
            i for i, entry in enumerate(self._entries) if self.is_entry_available(entry)
        }
        self._filter_text = ""

        self._set_status("ready")
        self.analysis_completed.emit()
        self.cleanup_worker()

    def _on_worker_failed(self, error_msg: str):
        self._error_message = error_msg
        self._set_status("failed")
        self.analysis_failed.emit(error_msg)
        self.cleanup_worker()

    def _on_worker_cancelled(self):
        self._set_status("idle")
        self.cleanup_worker()

    def _set_status(self, status: str):
        self._analysis_status = status
        self.is_loading = status in ("fetching", "analyzing")
        self.state_changed.emit()

    @staticmethod
    def _format_duration(seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.workers.search_worker import SearchWorker
from typing import List

class HomeViewModel(BaseViewModel):
    """
    ViewModel for the Home Screen.
    Handles search initiation, progress, and recent search history.
    """
    # Custom signals for Home Screen
    search_initiated = Signal(str)
    search_completed = Signal(object) # Dictionary of compilations and playlists
    search_failed = Signal(str)
    search_progress_updated = Signal(float, str)
    search_cancelled = Signal()
    history_updated = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent_searches: List[str] = []
        self._search_progress: float = 0.0
        self._status_message: str = ""
        self._worker: SearchWorker = None

    @property
    def recent_searches(self) -> List[str]:
        return self._recent_searches

    @property
    def search_progress(self) -> float:
        return self._search_progress
        
    @property
    def status_message(self) -> str:
        return self._status_message

    def submit_query(self, query: str):
        """Initiates a search query via SearchWorker."""
        query = query.strip()
        if not query:
            return

        if self.is_loading:
            self.cancel_search()

        self._add_to_history(query)
        self.is_loading = True
        self._search_progress = 0.0
        self._status_message = "Starting search..."
        self.search_progress_updated.emit(0.0, self._status_message)
        self.search_initiated.emit(query)

        self._worker = SearchWorker(query)
        self._worker.progress.connect(self._on_search_progress)
        self._worker.completed.connect(self._on_search_completed)
        self._worker.failed.connect(self._on_search_failed)
        self._worker.cancelled.connect(self._on_search_cancelled)
        self._worker.start()

    def cancel_search(self):
        """Cancels an ongoing search."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_message = "Cancelling..."
            self.search_progress_updated.emit(self._search_progress, self._status_message)

    def clear_history(self):
        """Clears recent search history."""
        self._recent_searches.clear()
        self.history_updated.emit(self._recent_searches)

    def _add_to_history(self, query: str):
        """Adds a query to recent searches."""
        if query in self._recent_searches:
            self._recent_searches.remove(query)
        self._recent_searches.insert(0, query)
        self._recent_searches = self._recent_searches[:10]
        self.history_updated.emit(self._recent_searches)

    def _on_search_progress(self, message: str, percent: float):
        self._search_progress = percent
        self._status_message = message
        self.search_progress_updated.emit(percent, message)

    def _on_search_completed(self, results):
        self.is_loading = False
        self._worker = None
        self._search_progress = 1.0
        self._status_message = "Done"
        self.search_completed.emit(results)

    def _on_search_failed(self, error: str):
        self.is_loading = False
        self._worker = None
        self._status_message = f"Error: {error}"
        self.search_failed.emit(error)

    def _on_search_cancelled(self):
        self.is_loading = False
        self._worker = None
        self._status_message = "Search cancelled"
        self.search_cancelled.emit()

from typing import Dict, List, Any, Optional
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.core.service_container import ServiceContainer


class ResultsCenterViewModel(BaseViewModel):
    """
    ViewModel for the Results Center Screen.
    Reads historical completed and failed jobs from ResultStore.
    Provides filtering, searching, and folder-open capabilities.
    No write or execution operations are performed.
    """

    # Emitted when visible results change (filter / search / refresh)
    results_updated = Signal()

    # Statuses available for filtering
    FILTER_ALL = "ALL"
    FILTER_COMPLETED = "COMPLETED"
    FILTER_FAILED = "FAILED"

    def __init__(self, parent=None):
        super().__init__(parent)

        container = ServiceContainer()
        self._result_store = container.result_store

        # --- Raw data from store ---
        self._all_records: List[Dict[str, Any]] = []

        # --- State ---
        self._search_query: str = ""
        self._active_filter: str = self.FILTER_ALL

    # ------------------------------------------------------------------
    # Public state properties
    # ------------------------------------------------------------------

    @property
    def search_query(self) -> str:
        return self._search_query

    @property
    def active_filter(self) -> str:
        return self._active_filter

    @property
    def completed_jobs(self) -> List[Dict[str, Any]]:
        return [r for r in self._all_records if r.get("status") == "COMPLETED"]

    @property
    def failed_jobs(self) -> List[Dict[str, Any]]:
        return [r for r in self._all_records if r.get("status") == "FAILED"]

    @property
    def exported_tracks(self) -> List[str]:
        """Flat list of all exported file paths across completed jobs."""
        tracks: List[str] = []
        for record in self.completed_jobs:
            tracks.extend(record.get("result_files", []))
        return tracks

    @property
    def visible_records(self) -> List[Dict[str, Any]]:
        """Records after applying the current filter and search query."""
        records = self._all_records

        # Apply status filter
        if self._active_filter != self.FILTER_ALL:
            records = [r for r in records if r.get("status") == self._active_filter]

        # Apply search query (title or source_type)
        if self._search_query.strip():
            q = self._search_query.strip().lower()
            records = [
                r for r in records
                if q in (r.get("title") or "").lower()
                or q in (r.get("source_type") or "").lower()
            ]

        return records

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def load_history(self):
        """Fetch all records from ResultStore and refresh the UI."""
        self.is_loading = True
        try:
            self._all_records = self._result_store.retrieve_history()
        except Exception as exc:
            self.error_occurred.emit(f"Failed to load history: {exc}")
            self._all_records = []
        finally:
            self.is_loading = False
        self.results_updated.emit()

    def set_search_query(self, query: str):
        """Update the active search query and refresh visible results."""
        if self._search_query != query:
            self._search_query = query
            self.results_updated.emit()

    def set_filter(self, status: str):
        """
        Set active status filter.
        Accepts: FILTER_ALL, FILTER_COMPLETED, FILTER_FAILED.
        """
        if status not in (self.FILTER_ALL, self.FILTER_COMPLETED, self.FILTER_FAILED):
            self.error_occurred.emit(f"Unknown filter: {status}")
            return
        if self._active_filter != status:
            self._active_filter = status
            self.results_updated.emit()

    def delete_record(self, job_id: str):
        """Remove a record from the persistent store and refresh."""
        try:
            self._result_store.delete_record(job_id)
            self._all_records = [r for r in self._all_records if r.get("id") != job_id]
            self.results_updated.emit()
        except Exception as exc:
            self.error_occurred.emit(f"Failed to delete record: {exc}")

    def clear_all(self):
        """Remove all records from the persistent store and refresh."""
        try:
            self._result_store.clear_all_records()
            self._all_records = []
            self.results_updated.emit()
        except Exception as exc:
            self.error_occurred.emit(f"Failed to clear history: {exc}")

    def open_output_folder(self, job_id: str):
        """
        Open the output folder for the given job in the OS file explorer.
        Resolves the folder from the first result_file path in the record.
        """
        import subprocess
        import sys
        from pathlib import Path

        record = next((r for r in self._all_records if r.get("id") == job_id), None)
        if not record:
            self.error_occurred.emit(f"Job {job_id} not found.")
            return

        files = record.get("result_files", [])
        if not files:
            self.error_occurred.emit("No output files available for this job.")
            return

        folder = str(Path(files[0]).parent)

        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", folder], shell=False)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder], shell=False)
            else:
                subprocess.Popen(["xdg-open", folder], shell=False)
        except Exception as exc:
            self.error_occurred.emit(f"Could not open folder: {exc}")

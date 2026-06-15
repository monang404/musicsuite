from typing import Dict, List, Optional
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from engines.search.ranking.ranking import RankedGroup
from engines.search.models.search_entity import SearchEntity

class ResultsViewModel(BaseViewModel):
    """
    ViewModel for the Results Screen.
    Manages the state of search results, filtering, sorting, and source selection.
    """
    # Signals
    results_loaded = Signal()
    source_selected = Signal(object) # SearchEntity
    filter_applied = Signal(str)
    sort_applied = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._compilations: List[RankedGroup] = []
        self._playlists: List[RankedGroup] = []
        self._selected_source: Optional[SearchEntity] = None
        self._active_filter: str = ""
        self._active_sort: str = "Relevance"

    @property
    def compilations(self) -> List[RankedGroup]:
        return self._compilations

    @property
    def playlists(self) -> List[RankedGroup]:
        return self._playlists

    @property
    def selected_source(self) -> Optional[SearchEntity]:
        return self._selected_source

    @property
    def active_filter(self) -> str:
        return self._active_filter

    @property
    def active_sort(self) -> str:
        return self._active_sort

    def load_results(self, payload: Dict[str, List[RankedGroup]]):
        """Loads the results payload and triggers UI refresh."""
        self._compilations = payload.get("compilations", [])
        
        pl = payload.get("playlists", [])
        if pl is None:
            self.playlist_failed = True
            self._playlists = []
        else:
            self.playlist_failed = False
            self._playlists = pl
            
        self.state_changed.emit()
        self.results_loaded.emit()

    def select_source(self, source: SearchEntity):
        """Selects a source and triggers navigation event."""
        self._selected_source = source
        self.state_changed.emit()
        self.source_selected.emit(source)

    def apply_filter(self, filter_term: str):
        """Applies a filter term to the results."""
        self._active_filter = filter_term
        self.state_changed.emit()
        self.filter_applied.emit(filter_term)

    def apply_sort(self, sort_order: str):
        """Applies a sort order to the results."""
        self._active_sort = sort_order
        self.state_changed.emit()
        self.sort_applied.emit(sort_order)

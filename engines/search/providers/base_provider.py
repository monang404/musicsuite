from abc import ABC, abstractmethod
from typing import List
from engines.search.models.compilation_source import CompilationVideo

class ProviderUnavailableError(Exception):
    pass

class BaseProvider(ABC):

    @abstractmethod
    def search_fast(self, queries: List[str], result_count: int = 15) -> List[CompilationVideo]:
        """Fase 1: ambil metadata ringan dari banyak kandidat."""
        pass

    @abstractmethod
    def fetch_full(self, url: str) -> CompilationVideo:
        """Fase 2: deep fetch satu source, populate chapters + description."""
        pass

    @abstractmethod
    def search_playlists(self, queries: List[str]) -> List["PlaylistSource"]:
        """Fase 1: ambil metadata ringan dari banyak kandidat playlist."""
        pass

    @abstractmethod
    def fetch_playlist_full(self, playlist_url: str) -> "PlaylistSource":
        """Fase 2: deep fetch satu playlist."""
        pass

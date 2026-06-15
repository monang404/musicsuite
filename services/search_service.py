from typing import List, Dict

from engines.search.service import SearchEngineService
from engines.search.models.compilation_source import CompilationVideo
from engines.search.ranking.ranking import RankedGroup
from services.security import validate_url
from services.url_classifier import classify_url
from engines.search.ranking.playlist_filter import PlaylistFilter
from engines.search.ranking.playlist_scorer import PlaylistScorer

class SearchService:
    """
    Service layer orchestrator for Search Engine.
    Provides a clean facade over the underlying engine implementation.
    """
    def __init__(self, engine: SearchEngineService = None):
        self.engine = engine or SearchEngineService()

    def search(self, query: str) -> List[RankedGroup]:
        """
        Performs a basic search.
        """
        return self.engine.search_single_query(query)

    def search_playlist(self, query: str) -> List[RankedGroup]:
        """
        Performs a playlist specific search.
        """
        return self.engine.search_playlist(query)

    def search_compilation(self, query: str) -> List[RankedGroup]:
        """
        Performs a compilation/album specific search with query expansion.
        """
        return self.engine.search_compilation(query)

    def fetch_metadata(self, url: str) -> CompilationVideo:
        """
        Fetches full metadata for a single source URL.
        Delegates to the engine provider's deep fetch mechanism.
        
        Args:
            url: The URL of the source to fetch metadata for.
            
        Returns:
            A fully populated CompilationVideo object with tracks, chapters, etc.
        """
        validate_url(url)
        return self.engine.provider.fetch_full(url)

    def fetch_playlist_metadata(self, url: str):
        """
        Fetches full metadata for a playlist URL.
        """
        validate_url(url)
        return self.engine.provider.fetch_playlist_full(url)

    def rank_results(self, results: List[CompilationVideo]) -> List[RankedGroup]:
        """
        Ranks arbitrary sources using the engine's ranking mechanism.
        """
        return self.engine.rank_results(results)

    def resolve_query(self, query: str) -> Dict[str, List[RankedGroup]]:
        """
        Intelligently resolves a text query or a direct URL.
        Internally orchestrates compilation and playlist searches.
        Returns a dictionary containing:
        {
            "compilations": List[RankedGroup],
            "playlists": List[RankedGroup]
        }
        """
        import concurrent.futures

        is_url = query.startswith("http://") or query.startswith("https://")

        if is_url:
            validate_url(query)
            url_type = classify_url(query)
            if url_type == "playlist":
                playlist = self.engine.provider.fetch_playlist_full(query)
                filtered = PlaylistFilter().apply([playlist])
                quality = {p.id: PlaylistScorer("").score_phase2(p) for p in filtered}
                results = self.engine.rank_results(filtered, quality)
                return {"compilations": [], "playlists": results}
            else:
                results = self.search(query)
                return {"compilations": results, "playlists": []}
                
        # If it's a keyword query, orchestrate both searches concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_comp = executor.submit(self.search_compilation, query)
            future_play = executor.submit(self.search_playlist, query)

            try:
                compilations = future_comp.result()
            except Exception:
                compilations = []

            try:
                playlists = future_play.result()
            except Exception:
                playlists = []

        return {
            "compilations": compilations,
            "playlists": playlists
        }

import concurrent.futures
import logging
from typing import List, Dict

from engines.search.providers.ytdlp_provider import YtdlpProvider
from engines.search.providers.base_provider import BaseProvider
from engines.search.ranking.compilation_scorer import CompilationScorer
from engines.search.ranking.ranking import RankingEngine, RankedGroup
from engines.search.ranking.compilation_filter import CompilationFilter
from engines.search.ranking.playlist_filter import PlaylistFilter
from engines.search.discovery.query_expander import QueryExpander
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.playlist_source import PlaylistSource
from engines.search.models.search_entity import SearchEntity
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.playlist_scorer import PlaylistScorer

class SearchEngineService:
    def __init__(self, provider: BaseProvider = None):
        self.provider = provider or YtdlpProvider()
        self.expander = QueryExpander()
        self.filter = CompilationFilter()
        self.ranking = RankingEngine()

    def search_compilation(self, query: str) -> List[RankedGroup]:
        """
        Executes a deep compilation search (expands query).
        """
        queries = self.expander.expand(query)
        return self._run_compilation_pipeline(query, queries)

    def search_single_query(self, query: str) -> List[RankedGroup]:
        """
        Executes a search using a single direct query.
        """
        return self._run_compilation_pipeline(query, [query])

    def search_playlist(self, query: str) -> List[RankedGroup]:
        """
        Executes a playlist search. Modifies query to specifically target playlists.
        """
        queries = self.expander.expand_playlist(query)
        return self._run_playlist_pipeline(query, queries)

    def _run_compilation_pipeline(self, base_term: str, queries: List[str]) -> List[RankedGroup]:
        raw_sources = self.provider.search_fast(queries)
        filtered = self.filter.apply(raw_sources)

        scorer = CompilationScorer(base_term)
        quality_results: Dict[str, QualityResult] = {
            s.id: scorer.score_phase1(s)
            for s in filtered
        }

        # Sort and take top 5
        filtered_sorted = sorted(filtered, key=lambda s: quality_results[s.id].score, reverse=True)
        top_candidates = filtered_sorted[:5]

        # Phase 2: Deep Fetch
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {executor.submit(self.provider.fetch_full, s.url): s for s in top_candidates}
            for future in concurrent.futures.as_completed(future_to_source):
                original_s = future_to_source[future]
                try:
                    full_s = future.result()
                    full_s.id = original_s.id
                    
                    idx = top_candidates.index(original_s)
                    top_candidates[idx] = full_s
                    quality_results[full_s.id] = scorer.score_phase2(full_s)
                except Exception as e:
                    logging.error("Failed to fetch full source in phase 2", exc_info=True)

        return self.rank_results(top_candidates, quality_results)

    # Alias for backward compatibility
    _run_search_pipeline = _run_compilation_pipeline

    def _run_playlist_pipeline(self, base_term: str, queries: List[str]) -> List[RankedGroup]:
        raw_playlists = self.provider.search_playlists(queries)
        playlist_filter = PlaylistFilter()
        filtered = playlist_filter.apply(raw_playlists)

        scorer = PlaylistScorer(base_term)
        quality_results = {p.id: scorer.score_phase1(p) for p in filtered}

        filtered_sorted = sorted(filtered, key=lambda p: quality_results[p.id].score, reverse=True)
        top_candidates = filtered_sorted[:5]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_p = {executor.submit(self.provider.fetch_playlist_full, p.url): p for p in top_candidates}
            for future in concurrent.futures.as_completed(future_to_p):
                original = future_to_p[future]
                try:
                    full = future.result()
                    full.id = original.id
                    idx = top_candidates.index(original)
                    top_candidates[idx] = full
                except Exception:
                    logging.error("Failed to fetch full playlist in phase 2", exc_info=True)

        # re-apply filter (item_count < 3 and possible entry-level patterns)
        final_candidates = playlist_filter.apply(top_candidates)
        
        # Phase 2 score using the fetched entry titles
        for p in final_candidates:
            quality_results[p.id] = scorer.score_phase2(p)

        return self.rank_results(final_candidates, quality_results)

    def rank_results(self, sources: List[SearchEntity], quality_results: Dict[str, QualityResult] = None) -> List[RankedGroup]:
        """
        Ranks results. If quality_results is not provided, it generates phase 2 scores.
        """
        if quality_results is None:
            # Fallback for compilation, handled slightly differently
            scorer = CompilationScorer("") 
            quality_results = {s.id: scorer.score_phase2(s) for s in sources}
            
        return self.ranking.rank(sources, quality_results)

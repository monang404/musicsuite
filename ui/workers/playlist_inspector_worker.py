from typing import Dict, List, Optional, Any
import logging
from ui.workers.base_worker import BaseWorker
from ui.core.service_container import ServiceContainer
from engines.search.models.playlist_source import PlaylistSource
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.playlist_scorer import PlaylistScorer

class PlaylistInspectorWorker(BaseWorker):
    """
    Worker for performing playlist metadata fetch and analysis
    in a background thread.
    """
    def __init__(self, source: PlaylistSource, parent=None):
        super().__init__(parent)
        self.source = source
        container = ServiceContainer()
        self.search_service = container.search_service

    def _execute_work(self):
        if self.is_cancelled():
            self.cancelled.emit()
            return

        self.progress.emit("Starting playlist analysis...", 0.1)

        try:
            # Step 1: Deep fetch if needed
            fetched_source = self.source
            if not self.source.is_deep_fetched:
                self.progress.emit("Fetching playlist metadata...", 0.3)
                fetched_source = self.search_service.fetch_playlist_metadata(self.source.url)
                fetched_source.id = self.source.id

            if self.is_cancelled():
                self.cancelled.emit()
                return

            # Step 2: Build metadata dict
            self.progress.emit("Building metadata...", 0.6)
            metadata = self._build_metadata(fetched_source)

            # Step 3: Extract entries
            entries = list(fetched_source.entries) if fetched_source.entries else []

            if self.is_cancelled():
                self.cancelled.emit()
                return

            # Step 4: Calculate confidence score
            self.progress.emit("Analyzing confidence...", 0.8)
            confidence_score = self._calculate_confidence(fetched_source)

            if self.is_cancelled():
                self.cancelled.emit()
                return

            # Construct output DTO dict
            result_dto = {
                "source": fetched_source,
                "metadata": metadata,
                "entries": entries,
                "confidence_score": confidence_score
            }

            self.progress.emit("Analysis complete", 1.0)
            self.completed.emit(result_dto)

        except Exception as e:
            if not self.is_cancelled():
                self.failed.emit(str(e))
                raise e

    def _build_metadata(self, s: PlaylistSource) -> Dict[str, Any]:
        """Builds a metadata dictionary from the playlist source."""
        metadata = {
            "title": s.title,
            "channel": s.channel,
            "url": s.url,
            "upload_date": s.upload_date,
            "thumbnail_url": s.thumbnail_url,
            "item_count": s.item_count,
            "is_official": s.is_official,
            "is_deep_fetched": s.is_deep_fetched,
        }
        return metadata

    def _calculate_confidence(self, s: PlaylistSource) -> Optional[QualityResult]:
        """Calculates the confidence score using PlaylistScorer."""
        try:
            scorer = PlaylistScorer("")
            res = scorer.score_phase2(s)
            return res
        except Exception:
            logging.error("Failed to calculate confidence score", exc_info=True)
        return None

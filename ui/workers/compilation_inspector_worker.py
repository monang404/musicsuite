from typing import Dict, List, Optional, Any
import logging
from ui.workers.base_worker import BaseWorker
from ui.core.service_container import ServiceContainer
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.track import Track
from engines.search.models.quality_result import QualityResult

class CompilationInspectorWorker(BaseWorker):
    """
    Worker for performing source metadata fetch and timestamp analysis (confidence scoring)
    in a background thread.
    """
    def __init__(self, source: CompilationVideo, parent=None):
        super().__init__(parent)
        self.source = source
        container = ServiceContainer()
        self.search_service = container.search_service

    def _execute_work(self):
        """
        Executes the background analysis:
        1. Deep fetch metadata if needed
        2. Build metadata dict
        3. Extract tracks
        4. Build timestamp text
        5. Calculate confidence score
        """
        if self.is_cancelled():
            self.cancelled.emit()
            return

        self.progress.emit("Starting analysis...", 0.1)

        try:
            # Step 1: Deep fetch if needed
            fetched_source = self.source
            if not self.source.is_deep_fetched:
                self.progress.emit("Fetching metadata...", 0.3)
                fetched_source = self.search_service.fetch_metadata(self.source.url)
                # Preserve original ID
                fetched_source.id = self.source.id

            if self.is_cancelled():
                self.cancelled.emit()
                return

            # Step 2: Build metadata dict
            self.progress.emit("Building metadata...", 0.5)
            metadata = self._build_metadata(fetched_source)

            # Step 3: Extract tracks
            tracks = list(fetched_source.tracks) if fetched_source.tracks else []

            # Step 4: Build timestamp text from tracks
            timestamps = self._build_timestamp_text(tracks)

            if self.is_cancelled():
                self.cancelled.emit()
                return

            # Step 5: Calculate confidence score
            self.progress.emit("Analyzing timestamps...", 0.8)
            confidence_score = self._calculate_confidence(fetched_source)

            if self.is_cancelled():
                self.cancelled.emit()
                return

            # Construct output DTO dict
            result_dto = {
                "source": fetched_source,
                "metadata": metadata,
                "tracks": tracks,
                "timestamps": timestamps,
                "confidence_score": confidence_score
            }

            self.progress.emit("Analysis complete", 1.0)
            self.completed.emit(result_dto)

        except Exception as e:
            if not self.is_cancelled():
                raise e

    def _build_metadata(self, s: CompilationVideo) -> Dict[str, Any]:
        """Builds a metadata dictionary from the source."""
        metadata = {
            "title": s.title,
            "channel": s.channel,
            "url": s.url,
            "duration": s.duration,
            "duration_formatted": self._format_duration(s.duration),
            "view_count": s.view_count,
            "upload_date": s.upload_date,
            "thumbnail_url": s.thumbnail_url,
            "track_count": s.track_count,
            "chapter_count": s.chapter_count,
            "timestamp_count": s.timestamp_count,
            "has_chapters": s.has_chapters,
            "has_timestamps": s.has_timestamps,
            "chapters_cover_full_duration": s.chapters_cover_full_duration,
            "timestamps_are_monotonic": s.timestamps_are_monotonic,
            "is_deep_fetched": s.is_deep_fetched,
        }

        # Duration statistics
        if s.track_count > 0:
            avg_duration = s.duration / s.track_count
            metadata["avg_track_duration"] = avg_duration
            metadata["avg_track_duration_formatted"] = self._format_duration(int(avg_duration))
        else:
            metadata["avg_track_duration"] = 0
            metadata["avg_track_duration_formatted"] = "N/A"

        return metadata

    def _build_timestamp_text(self, tracks: List[Track]) -> str:
        """Builds timestamp text from the track list."""
        if not tracks:
            return ""

        lines = []
        for track in tracks:
            time_str = self._format_duration(int(track.start_time))
            lines.append(f"{time_str}|{track.title}")
        return "\n".join(lines)

    def _calculate_confidence(self, s: CompilationVideo) -> Optional[QualityResult]:
        """Calculates the confidence score using the search service ranking."""
        try:
            ranked_groups = self.search_service.rank_results([s])
            if ranked_groups and ranked_groups[0].quality_results:
                return ranked_groups[0].quality_results.get(s.id)
        except Exception:
            logging.error("Failed to calculate confidence score", exc_info=True)
        return None

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Formats seconds into H:MM:SS or MM:SS."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

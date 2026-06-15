from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.shared_scoring import recency_bonus

class CompilationScorer:
    def __init__(self, artist: str = ""):
        self.artist = artist.lower()

    def score_phase1(self, source: CompilationVideo) -> QualityResult:
        """Estimasi score dari metadata ringan saja (fase 1)."""
        components = {
            "chapter_score": 0,
            "timestamp_score": 0,
            "track_count_quality": 0,
            "duration_validation": 0,
            "artist_consistency": self._artist_score(source),
            "recency_bonus": recency_bonus(source.upload_date),
            "soft_penalty": -source.soft_penalty
        }
        
        base = 30 if source.duration > 600 else 10
        total = max(0, min(100, base + sum(components.values())))
        
        label = QualityResult.label_from_score(total)
        return QualityResult(
            source_id=source.id,
            score=total,
            label=label,
            is_estimate=True,
            breakdown=components
        )

    def score_phase2(self, source: CompilationVideo) -> QualityResult:
        """Score final setelah deep fetch."""
        components = {
            "chapter_score": self._chapter_score(source),
            "timestamp_score": self._timestamp_score(source),
            "track_count_quality": self._track_count_score(source),
            "duration_validation": self._duration_score(source),
            "artist_consistency": self._artist_score(source),
            "recency_bonus": recency_bonus(source.upload_date),
            "soft_penalty": -source.soft_penalty
        }
        
        total = self._compute_total(components)
        label = QualityResult.label_from_score(total)
        
        return QualityResult(
            source_id=source.id,
            score=total,
            label=label,
            is_estimate=False,
            breakdown=components
        )

    def _chapter_score(self, source: CompilationVideo) -> int:
        if not source.has_chapters:
            return 0
        n = source.chapter_count
        if n >= 10:   base = 35
        elif n >= 6:  base = 28
        elif n >= 3:  base = 20
        else:         return 0

        completeness_bonus = 10 if source.chapters_cover_full_duration else 0
        return min(45, base + completeness_bonus)

    def _timestamp_score(self, source: CompilationVideo) -> int:
        if not source.has_timestamps:
            return 0
        n = source.timestamp_count
        if n >= 10:   base = 22
        elif n >= 6:  base = 16
        elif n >= 3:  base = 10
        else:         return 0

        monotonic_bonus = 8 if source.timestamps_are_monotonic else 0
        return min(30, base + monotonic_bonus)

    def _track_count_score(self, source: CompilationVideo) -> int:
        n = source.track_count
        if 8 <= n <= 25:    return 10
        elif 5 <= n <= 35:  return 7
        elif 3 <= n <= 50:  return 4
        else:               return 1

    def _duration_score(self, source: CompilationVideo) -> int:
        if source.track_count == 0:
            return 0
        avg_seconds = source.duration / source.track_count
        if 150 <= avg_seconds <= 360:   return 8
        elif 90 <= avg_seconds <= 480:  return 5
        elif 60 <= avg_seconds <= 600:  return 2
        else:                           return 0

    def _artist_score(self, source: CompilationVideo) -> int:
        if not self.artist:
            return 0
        if self.artist in source.title.lower() or self.artist in source.channel.lower():
            return 5
        return 0

    def _compute_total(self, components: dict) -> int:
        total = sum(components.values())
        return max(0, min(100, total))

# Alias for backward compatibility
CompilationScorer = CompilationScorer

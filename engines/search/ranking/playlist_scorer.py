"""
PlaylistScorer — Weighted relevance scoring for playlist search results.

Formula
-------
final_score (0–100) =
    artist_confidence * 45
  + music_score       * 35
  + metadata_quality  * 15
  + size_score        *  5

All sub-scores are normalised to [0.0, 1.0] before weighting.
"""

from typing import List

from engines.search.models.playlist_source import PlaylistSource, PlaylistEntry
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.shared_scoring import recency_bonus
from engines.search.ranking.playlist_music_classifier import PlaylistMusicClassifier
from engines.search.ranking.artist_entity_verifier import ArtistEntityVerifier
from engines.search.ranking.playlist_debug_reporter import PlaylistDebugReporter, CandidateReport

_music_clf = PlaylistMusicClassifier()
_artist_vrf = ArtistEntityVerifier()
_reporter = PlaylistDebugReporter()

# Weight constants (must sum to 1.0)
W_ARTIST   = 0.45
W_MUSIC    = 0.35
W_METADATA = 0.15
W_SIZE     = 0.05


class PlaylistScorer:
    def __init__(self, query: str = ""):
        self.query = query.strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_phase1(self, playlist: PlaylistSource) -> QualityResult:
        """
        Phase-1: uses title + channel only (no entry titles).
        Fast — no network calls needed.
        """
        music_result = _music_clf.classify(
            title=playlist.title,
            channel=playlist.channel,
            entry_titles=[],
        )
        artist_result = _artist_vrf.verify(
            artist_query=self.query,
            playlist_title=playlist.title,
            playlist_channel=playlist.channel,
            sample_entry_titles=[],
        )

        music_score     = music_result.music_score
        artist_conf     = artist_result.score
        metadata_qual   = self._metadata_quality(playlist)
        size_score      = 0.0   # unknown before deep fetch

        final_norm = (
            artist_conf   * W_ARTIST +
            music_score   * W_MUSIC  +
            metadata_qual * W_METADATA +
            size_score    * W_SIZE
        )
        final_int = max(0, min(100, round(final_norm * 100)))
        label = QualityResult.label_from_score(final_int)

        # Persist scores on the model for debug reporter
        playlist.music_score       = music_score
        playlist.artist_confidence = artist_conf
        playlist.metadata_quality  = metadata_qual

        breakdown = {
            "artist_confidence": artist_conf,
            "music_score":       music_score,
            "metadata_quality":  metadata_qual,
            "size_score":        size_score,
            "artist_reason":     artist_result.reason,
            "music_note":        music_result.note,
        }

        return QualityResult(
            source_id=playlist.id,
            score=final_int,
            label=label,
            is_estimate=True,
            breakdown=breakdown,
        )

    def score_phase2(self, playlist: PlaylistSource) -> QualityResult:
        """
        Phase-2: re-scores with entry titles from the deep-fetched playlist.
        """
        entry_titles = [e.title for e in (playlist.entries or [])[:20]]

        music_result = _music_clf.classify(
            title=playlist.title,
            channel=playlist.channel,
            entry_titles=entry_titles,
        )
        artist_result = _artist_vrf.verify(
            artist_query=self.query,
            playlist_title=playlist.title,
            playlist_channel=playlist.channel,
            sample_entry_titles=entry_titles,
        )

        music_score     = music_result.music_score
        artist_conf     = artist_result.score
        metadata_qual   = self._metadata_quality(playlist)
        size_score      = self._size_score(playlist)

        final_norm = (
            artist_conf   * W_ARTIST +
            music_score   * W_MUSIC  +
            metadata_qual * W_METADATA +
            size_score    * W_SIZE
        )
        final_int = max(0, min(100, round(final_norm * 100)))
        label = QualityResult.label_from_score(final_int)

        # Update model fields
        playlist.music_score       = music_score
        playlist.artist_confidence = artist_conf
        playlist.metadata_quality  = metadata_qual

        breakdown = {
            "artist_confidence": artist_conf,
            "music_score":       music_score,
            "metadata_quality":  metadata_qual,
            "size_score":        size_score,
            "artist_reason":     artist_result.reason,
            "music_note":        music_result.note,
        }

        return QualityResult(
            source_id=playlist.id,
            score=final_int,
            label=label,
            is_estimate=False,
            breakdown=breakdown,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _metadata_quality(self, playlist: PlaylistSource) -> float:
        """
        Combines official channel signal + recency bonus → [0.0, 1.0].
        """
        score = 0.0
        if playlist.is_official:
            score += 0.70
        recency = recency_bonus(playlist.upload_date)  # 0 or 5
        score += recency / 100.0  # normalise to 0–0.05
        return min(1.0, score)

    def _size_score(self, playlist: PlaylistSource) -> float:
        """
        Normalised playlist size score → [0.0, 1.0].
        Optimal range: 8–40 tracks.
        """
        n = playlist.item_count
        if n == 0:
            return 0.0
        if 8 <= n <= 40:
            return 1.0
        if 5 <= n <= 60:
            return 0.70
        if 3 <= n <= 100:
            return 0.40
        if n > 100:
            return 0.20   # very large playlists may be grab-bags
        return 0.0

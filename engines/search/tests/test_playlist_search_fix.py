"""
Tests for PLAYLIST_SEARCH_FIX.md requirements.

1. search_playlist uses 5-7 queries (from expand_playlist), not 1.
2. Short-duration "Official Playlist" videos are NOT dropped by PlaylistFilter.
3. search_playlist still returns results when some queries fail/timeout.
4. expand_playlist returns entries with playlist/mix/nonstop keywords.
5. score_phase1 gives a higher score to a playlist with "playlist" in title/channel
   vs. one without, given the same duration-equivalent metadata.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from engines.search.discovery.query_expander import QueryExpander
from engines.search.ranking.playlist_filter import PlaylistFilter
from engines.search.ranking.playlist_scorer import PlaylistScorer
from engines.search.models.playlist_source import PlaylistSource
from engines.search.service import SearchEngineService


# ── Test 1: search_playlist sends 5-7 queries ────────────────────────────────

@patch("engines.search.providers.ytdlp_provider.YtdlpProvider.fetch_playlist_full")
@patch("engines.search.providers.ytdlp_provider.YtdlpProvider.search_playlists")
def test_search_playlist_uses_multiple_queries(mock_search_playlists, mock_fetch_full):
    """search_playlist must call provider.search_playlists with 5-7 queries."""
    mock_search_playlists.return_value = []
    mock_fetch_full.return_value = None

    service = SearchEngineService()
    service.search_playlist("wali")

    assert mock_search_playlists.called, "search_playlists should have been called"
    queries_sent = mock_search_playlists.call_args[0][0]
    assert 5 <= len(queries_sent) <= 7, (
        f"Expected 5-7 queries, got {len(queries_sent)}: {queries_sent}"
    )


# ── Test 2: PlaylistFilter does not drop short videos with "playlist" title ──

def test_playlist_filter_keeps_short_playlist_videos():
    """Short-duration PlaylistSource titled 'Wali Official Playlist Full Album'
    should NOT be filtered out by PlaylistFilter (no album-duration check)."""
    pl = PlaylistSource(
        id="PL_SHORT",
        url="https://youtube.com/playlist?list=abc",
        title="Wali Official Playlist Full Album",
        channel="Wali",
        item_count=0,  # not yet deep-fetched
    )
    f = PlaylistFilter()
    result = f.apply([pl])
    assert len(result) == 1, (
        "PlaylistFilter should NOT drop 'Official Playlist' entries regardless of duration"
    )


# ── Test 3: search_playlist resilient to partial query failures ──────────────

@patch("engines.search.providers.ytdlp_provider.YtdlpProvider.fetch_playlist_full")
@patch("engines.search.providers.ytdlp_provider.YtdlpProvider.search_playlists")
def test_search_playlist_resilient_to_partial_failure(mock_search_playlists, mock_fetch_full):
    """search_playlist should still return results if search_playlists internally
    handles some individual query failures (i.e. raises on some, succeeds on others).
    The pipeline must not be empty if at least one successful playlist is found."""
    good_pl = PlaylistSource(
        id="PL_GOOD",
        url="https://youtube.com/playlist?list=good",
        title="Wali Official Playlist",
        channel="Wali Official",
        item_count=0,
        is_official=True,
    )
    # Simulate provider returning 1 good result despite some internal query failures
    mock_search_playlists.return_value = [good_pl]

    full_pl = PlaylistSource(
        id="PL_GOOD",
        url="https://youtube.com/playlist?list=good",
        title="Wali Official Playlist",
        channel="Wali Official",
        item_count=10,
        is_official=True,
    )
    mock_fetch_full.return_value = full_pl

    service = SearchEngineService()
    result = service.search_playlist("wali")

    assert len(result) > 0, (
        "search_playlist should return results even when some queries fail"
    )


# ── Test 4: expand_playlist keywords ─────────────────────────────────────────

def test_expand_playlist_contains_playlist_mix_nonstop():
    """Every entry from expand_playlist should contain 'playlist', 'mix', or 'nonstop'."""
    expander = QueryExpander()
    results = expander.expand_playlist("wali")
    assert len(results) > 0, "expand_playlist should return at least one query"
    for q in results:
        has_keyword = any(kw in q.lower() for kw in ("playlist", "mix", "nonstop"))
        assert has_keyword, f"Query missing playlist/mix/nonstop keyword: '{q}'"


# ── Test 5: phase-1 score boost for "playlist" in title/channel ──────────────

def test_playlist_scorer_phase1_boost_for_playlist_signal():
    """A PlaylistSource with 'playlist' in title should score higher in phase-1
    than an otherwise identical source without that signal."""
    scorer = PlaylistScorer("wali")

    pl_with_signal = PlaylistSource(
        id="A",
        url="http://a",
        title="Wali Playlist Terbaik",
        channel="Wali",
        item_count=0,
    )
    pl_without_signal = PlaylistSource(
        id="B",
        url="http://b",
        title="Wali Lagu Terbaik",
        channel="Wali",
        item_count=0,
    )

    score_with = scorer.score_phase1(pl_with_signal).score
    score_without = scorer.score_phase1(pl_without_signal).score

    assert score_with > score_without, (
        f"Source with 'playlist' in title should score higher "
        f"({score_with} vs {score_without})"
    )

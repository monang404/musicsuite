import pytest
from engines.search.models.playlist_source import PlaylistSource, PlaylistEntry
from engines.search.ranking.playlist_scorer import PlaylistScorer

def test_score_phase1():
    pl = PlaylistSource(
        id="PL1",
        url="http",
        title="Wali Official Playlist",
        channel="Wali Band",
        is_official=True,
        upload_date="20230101"
    )
    
    scorer = PlaylistScorer("wali")
    res = scorer.score_phase1(pl)
    
    assert res.is_estimate is True
    assert res.score >= 60

def test_score_phase2():
    entries = [
        PlaylistEntry(title="T1", url="U1", duration=210),
        PlaylistEntry(title="T2", url="U2", duration=220),
        PlaylistEntry(title="T3", url="U3", duration=205),
        PlaylistEntry(title="T4", url="U4", duration=215),
        PlaylistEntry(title="T5", url="U5", duration=230),
        PlaylistEntry(title="T6", url="U6", duration=200),
        PlaylistEntry(title="T7", url="U7", duration=240),
        PlaylistEntry(title="T8", url="U8", duration=210),
    ]
    pl = PlaylistSource(
        id="PL2",
        url="http",
        title="Wali Full Album",
        channel="Wali",
        item_count=8,
        entries=entries,
        is_official=True,
        upload_date="20230101"
    )
    
    scorer = PlaylistScorer("wali")
    res = scorer.score_phase2(pl)
    
    assert res.is_estimate is False
    assert res.score >= 75
    assert res.label in ["Great", "Excellent"]
    
def test_playlist_scorer_no_compilation_fields():
    pl = PlaylistSource(
        id="PL3", url="http", title="Test", channel="Test", item_count=0
    )
    scorer = PlaylistScorer("test")
    # Will throw AttributeError if missing fields are accessed directly
    scorer.score_phase2(pl)

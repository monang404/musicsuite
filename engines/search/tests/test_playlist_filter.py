import pytest
from engines.search.models.playlist_source import PlaylistSource
from engines.search.ranking.playlist_filter import PlaylistFilter

def test_should_exclude():
    filter = PlaylistFilter()
    
    assert filter.should_exclude("Mix - Wali Songs") is True
    assert filter.should_exclude("Wali Radio") is True
    assert filter.should_exclude("Wali Karaoke Version") is True
    assert filter.should_exclude("Official Wali Playlist") is False

def test_apply():
    filter = PlaylistFilter()
    
    playlists = [
        PlaylistSource(id="1", url="u1", title="Official Wali Playlist", channel="channel", item_count=15),
        PlaylistSource(id="2", url="u2", title="Mix - Wali Songs", channel="channel", item_count=10),
        PlaylistSource(id="3", url="u3", title="Wali", channel="channel", item_count=2), # too few items after deep fetch
        PlaylistSource(id="4", url="u4", title="Wali Best", channel="channel", item_count=0), # phase 1, keep it
    ]
    
    filtered = filter.apply(playlists)
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "4"

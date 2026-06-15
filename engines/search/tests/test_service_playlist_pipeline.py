import pytest
from unittest.mock import patch, MagicMock
from engines.search.service import SearchEngineService
from engines.search.models.playlist_source import PlaylistSource
from engines.search.models.compilation_source import CompilationVideo

@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.search_playlists')
@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.fetch_playlist_full')
@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.search_fast')
@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.fetch_full')
def test_search_playlist_uses_playlist_pipeline(
    mock_fetch_full, mock_search_fast, mock_fetch_playlist_full, mock_search_playlists
):
    service = SearchEngineService()
    
    # Mock data
    pl = PlaylistSource(id="1", url="http://p1", title="Official Playlist", channel="channel", item_count=0)
    pl_full = PlaylistSource(id="1", url="http://p1", title="Official Playlist", channel="channel", item_count=5)
    
    mock_search_playlists.return_value = [pl]
    mock_fetch_playlist_full.return_value = pl_full
    
    result = service.search_playlist("wali")
    
    assert mock_search_playlists.called
    assert mock_fetch_playlist_full.called
    assert not mock_search_fast.called
    assert not mock_fetch_full.called
    
    assert len(result) > 0
    assert result[0].sources[0].id == "1"

@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.search_playlists')
@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.fetch_playlist_full')
@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.search_fast')
@patch('engines.search.providers.ytdlp_provider.YtdlpProvider.fetch_full')
def test_search_compilation_uses_compilation_pipeline(
    mock_fetch_full, mock_search_fast, mock_fetch_playlist_full, mock_search_playlists
):
    service = SearchEngineService()
    
    c = CompilationVideo(id="2", url="http://c2", title="Full Album", channel="channel", duration=3600)
    c_full = CompilationVideo(id="2", url="http://c2", title="Full Album", channel="channel", duration=3600, track_count=10)
    
    mock_search_fast.return_value = [c]
    mock_fetch_full.return_value = c_full
    
    result = service.search_compilation("wali")
    
    assert not mock_search_playlists.called
    assert not mock_fetch_playlist_full.called
    assert mock_search_fast.called
    assert mock_fetch_full.called
    
    assert len(result) > 0
    assert result[0].sources[0].id == "2"

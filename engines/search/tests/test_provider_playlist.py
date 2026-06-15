import pytest
from unittest.mock import patch, MagicMock
from engines.search.providers.ytdlp_provider import YtdlpProvider
from engines.search.models.playlist_source import PlaylistSource
from engines.search.models.compilation_source import CompilationVideo

@pytest.fixture
def provider():
    # Mock _check_ytdlp_available to avoid needing yt-dlp installed for unit tests
    with patch.object(YtdlpProvider, '_check_ytdlp_available', return_value=True):
        return YtdlpProvider()

@patch('subprocess.run')
def test_search_playlists(mock_run, provider):
    mock_result = MagicMock()
    mock_result.stdout = '{"ie_key": "YoutubePlaylist", "url": "https://youtube.com/playlist?list=PL123", "title": "Test Playlist"}\n{"url": "https://youtube.com/watch?v=abc", "title": "Test Video"}\n'
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    results = provider.search_playlists(["test"])
    
    assert len(results) == 1
    assert isinstance(results[0], PlaylistSource)
    assert results[0].url == "https://youtube.com/playlist?list=PL123"
    assert results[0].title == "Test Playlist"

@patch('subprocess.run')
def test_fetch_playlist_full(mock_run, provider):
    mock_result = MagicMock()
    mock_result.stdout = '{"id": "PL123", "url": "https://youtube.com/playlist?list=PL123", "title": "Full Playlist", "entries": [{"url": "https://youtube.com/watch?v=1", "duration": 100}, {"url": "https://youtube.com/watch?v=2", "duration": 200}]}'
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    with patch('engines.search.providers.ytdlp_provider.validate_url'):
        result = provider.fetch_playlist_full("https://youtube.com/playlist?list=PL123")
    
    assert isinstance(result, PlaylistSource)
    assert result.item_count == 2
    assert result.is_deep_fetched is True
    assert result.title == "Full Playlist"

@patch('subprocess.run')
def test_search_single(mock_run, provider):
    # Ensure existing _search_single returns CompilationVideo / CompilationVideo
    mock_result = MagicMock()
    mock_result.stdout = '{"url": "https://youtube.com/watch?v=abc", "title": "Test Video"}\n'
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    results = provider._search_single("test")
    
    assert len(results) == 1
    assert isinstance(results[0], CompilationVideo)
    assert results[0].title == "Test Video"

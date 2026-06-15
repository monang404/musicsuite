import pytest
import json
from unittest.mock import patch, MagicMock
import subprocess

from engines.search.providers.ytdlp_provider import YtdlpProvider, ProviderUnavailableError

@pytest.fixture
def mock_ytdlp_available():
    with patch('subprocess.run') as mock_run:
        # Mock yt-dlp --version success
        mock_run.return_value = MagicMock(returncode=0)
        yield mock_run

def test_ytdlp_unavailable():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(ProviderUnavailableError):
            YtdlpProvider()

def test_search_fast(mock_ytdlp_available):
    provider = YtdlpProvider()
    
    with patch('subprocess.run') as mock_run:
        # Mock search single result
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({
            "url": "https://youtube.com/watch?v=123",
            "title": "Mock Title",
            "uploader": "Mock Channel",
            "duration": 100
        }) + "\n" + json.dumps({
            "url": "https://youtube.com/watch?v=456",
            "title": "Mock Title 2",
            "uploader": "Mock Channel",
            "duration": 200
        })
        mock_run.return_value = mock_result
        
        sources = provider.search_fast(["query1"])
        
        assert len(sources) == 2
        assert sources[0].url == "https://youtube.com/watch?v=123"
        assert sources[1].url == "https://youtube.com/watch?v=456"

def test_search_fast_deduplicate(mock_ytdlp_available):
    provider = YtdlpProvider()
    
    with patch('subprocess.run') as mock_run:
        # Both queries return the exact same URL
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({
            "url": "https://youtube.com/watch?v=123",
            "title": "Mock Title",
            "uploader": "Mock Channel",
            "duration": 100
        })
        mock_run.return_value = mock_result
        
        # Parallel fetch will run subprocess.run twice and return duplicates
        sources = provider.search_fast(["query1", "query2"])
        
        # Should be deduplicated by url
        assert len(sources) == 1
        assert sources[0].url == "https://youtube.com/watch?v=123"

def test_fetch_full(mock_ytdlp_available):
    provider = YtdlpProvider()
    
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "url": "https://youtube.com/watch?v=123",
            "title": "Mock Album",
            "uploader": "Mock Channel",
            "duration": 600,
            "description": "00:00 Intro\n03:22 Song",
            "chapters": [
                {"start_time": 0, "end_time": 200, "title": "Intro"},
                {"start_time": 200, "end_time": 400, "title": "Song 1"},
                {"start_time": 400, "end_time": 600, "title": "Song 2"}
            ]
        })
        mock_run.return_value = mock_result
        
        source = provider.fetch_full("https://youtube.com/watch?v=123")
        
        assert source.is_deep_fetched is True
        # Tracklist priority: Chapters > Timestamps
        assert source.has_chapters is True
        assert source.chapter_count == 3
        assert source.track_count == 3
        assert source.tracks[0].title == "Intro"

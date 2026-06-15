import pytest
from unittest.mock import MagicMock
from services.search_service import SearchService
from engines.search.service import SearchEngineService

def test_search_service_search():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.search_single_query.return_value = ["mock_group"]
    
    service = SearchService(engine=mock_engine)
    result = service.search("artist name")
    
    mock_engine.search_single_query.assert_called_once_with("artist name")
    assert result == ["mock_group"]

def test_search_service_search_playlist():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.search_playlist.return_value = ["mock_playlist"]
    
    service = SearchService(engine=mock_engine)
    result = service.search_playlist("artist name")
    
    mock_engine.search_playlist.assert_called_once_with("artist name")
    assert result == ["mock_playlist"]

def test_search_service_search_compilation():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.search_compilation.return_value = ["mock_compilation"]
    
    service = SearchService(engine=mock_engine)
    result = service.search_compilation("artist name")
    
    mock_engine.search_compilation.assert_called_once_with("artist name")
    assert result == ["mock_compilation"]

def test_search_service_rank_results():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.rank_results.return_value = ["mock_ranked"]
    
    service = SearchService(engine=mock_engine)
    result = service.rank_results(["source1", "source2"])
    
    mock_engine.rank_results.assert_called_once_with(["source1", "source2"])
    assert result == ["mock_ranked"]

def test_search_service_resolve_query_keyword():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.search_compilation.return_value = ["mock_comp"]
    mock_engine.search_playlist.return_value = ["mock_play"]
    
    service = SearchService(engine=mock_engine)
    result = service.resolve_query("artist name")
    
    assert result == {"compilations": ["mock_comp"], "playlists": ["mock_play"]}
    mock_engine.search_compilation.assert_called_once_with("artist name")
    mock_engine.search_playlist.assert_called_once_with("artist name")

def test_search_service_resolve_query_url_video():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.search_single_query.return_value = ["mock_video"]
    
    service = SearchService(engine=mock_engine)
    result = service.resolve_query("https://youtube.com/watch?v=123")
    
    assert result == {"compilations": ["mock_video"], "playlists": []}
    mock_engine.search_single_query.assert_called_once_with("https://youtube.com/watch?v=123")

def test_search_service_resolve_query_url_playlist():
    mock_engine = MagicMock(spec=SearchEngineService)
    mock_engine.provider = MagicMock()
    mock_playlist = MagicMock()
    mock_playlist.id = "pl1"
    mock_playlist.title = "Mock Playlist"
    mock_playlist.item_count = 5
    mock_playlist.upload_date = "20230101"
    mock_engine.provider.fetch_playlist_full.return_value = mock_playlist
    mock_engine.rank_results.return_value = ["mock_ranked_playlist"]
    
    service = SearchService(engine=mock_engine)
    result = service.resolve_query("https://youtube.com/watch?v=123&list=456")
    
    assert result == {"compilations": [], "playlists": ["mock_ranked_playlist"]}
    mock_engine.provider.fetch_playlist_full.assert_called_once_with("https://youtube.com/watch?v=123&list=456")

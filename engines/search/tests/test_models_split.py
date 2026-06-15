import pytest
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.playlist_source import PlaylistSource, PlaylistEntry
from engines.search.models.compilation_source import CompilationVideo

def test_compilation_video_from_ytdlp_info():
    raw_json = {
        "id": "12345",
        "url": "https://youtube.com/watch?v=12345",
        "title": "Wali Terbaik",
        "uploader": "Wali Official",
        "duration": 3600,
        "view_count": 1000000,
        "upload_date": "20230101",
        "thumbnail": "https://img.youtube.com/vi/12345/0.jpg"
    }

    comp = CompilationVideo.from_ytdlp_info(raw_json)
    
    assert comp.url == "https://youtube.com/watch?v=12345"
    assert comp.title == "Wali Terbaik"
    assert comp.channel == "Wali Official"
    assert comp.duration == 3600
    assert comp.view_count == 1000000
    assert comp.upload_date == "20230101"
    assert comp.thumbnail_url == "https://img.youtube.com/vi/12345/0.jpg"
    assert comp.entity_type == "compilation"

def test_source_backward_compatibility():
    # CompilationVideo should be an alias for CompilationVideo
    assert CompilationVideo is CompilationVideo
    
def test_playlist_source_from_ytdlp_playlist_info():
    raw_json = {
        "id": "PL123",
        "url": "https://youtube.com/playlist?list=PL123",
        "title": "Wali Playlist Official",
        "uploader": "Wali Band",
        "entries": [
            {"title": "Track 1", "url": "https://youtube.com/watch?v=A", "duration": 200},
            {"title": "Track 2", "url": "https://youtube.com/watch?v=B", "duration": 250},
            {"title": "Track 3", "url": "https://youtube.com/watch?v=C", "duration": 300}
        ],
        "thumbnail": "https://img.youtube.com/vi/PL123/0.jpg"
    }
    
    pl = PlaylistSource.from_ytdlp_playlist_info(raw_json)
    
    assert pl.playlist_id == "PL123"
    assert pl.url == "https://youtube.com/playlist?list=PL123"
    assert pl.title == "Wali Playlist Official"
    assert pl.channel == "Wali Band"
    assert pl.item_count == 3
    assert len(pl.entries) == 3
    assert pl.is_official is True
    assert pl.entity_type == "playlist"
    
    assert pl.entries[0].title == "Track 1"
    assert pl.entries[0].url == "https://youtube.com/watch?v=A"
    assert pl.entries[0].duration == 200

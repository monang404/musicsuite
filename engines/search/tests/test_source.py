import pytest
import hashlib
from engines.search.models.compilation_source import CompilationVideo

def test_source_from_ytdlp_info():
    raw_data = {
        'url': 'https://www.youtube.com/watch?v=abcdefghijk',
        'title': 'Test Album',
        'uploader': 'Test Channel',
        'duration': 3600,
        'view_count': 1000000,
        'upload_date': '20230101'
    }
    
    source = CompilationVideo.from_ytdlp_info(raw_data)
    
    expected_id = hashlib.sha256('https://www.youtube.com/watch?v=abcdefghijk'.encode('utf-8')).hexdigest()[:8]
    
    assert source.id == expected_id
    assert source.url == 'https://www.youtube.com/watch?v=abcdefghijk'
    assert source.title == 'Test Album'
    assert source.channel == 'Test Channel'
    assert source.duration == 3600
    assert source.view_count == 1000000
    assert source.upload_date == '20230101'
    assert source.has_chapters is False
    assert source.is_deep_fetched is False

def test_source_from_ytdlp_info_missing_fields():
    raw_data = {
        'webpage_url': 'https://www.youtube.com/watch?v=123'
    }
    
    source = CompilationVideo.from_ytdlp_info(raw_data)
    assert source.url == 'https://www.youtube.com/watch?v=123'
    assert source.title == ''
    assert source.channel == ''
    assert source.duration == 0
    assert source.view_count == 0
    assert source.upload_date == ''

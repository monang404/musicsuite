import pytest
from engines.timestamp.service import TimestampService
from engines.timestamp.utils import AutoTimestampError

def test_service_chapters_fallback():
    # Mock video info with chapters
    info = {
        "chapters": [
            {"start_time": 0, "title": "Intro"},
            {"start_time": 180, "title": "Song A"}
        ]
    }
    
    # Should use chapters
    text, method = TimestampService.generate_timestamps("http://test", info)
    
    assert method == "chapters"
    assert "0:00|Intro" in text
    assert "03:00|Song A" in text

def test_service_description_fallback():
    # No chapters, but description has timestamps
    info = {
        "description": "0:00 Intro\n3:00 Song A"
    }
    
    text, method = TimestampService.generate_timestamps("http://test", info)
    
    assert method == "description"
    assert "0:00|Intro" in text
    assert "03:00|Song A" in text

def test_service_fails_when_empty():
    # Empty info, no chapters, no description, no comments
    info = {}
    
    with pytest.raises(AutoTimestampError):
        # Without audio path, it won't try silence detection, and if comments fail, it raises
        TimestampService.generate_timestamps("http://test_invalid", info)

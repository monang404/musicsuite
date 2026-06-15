import pytest
from engines.search.metadata.chapter_parser import ChapterParser

def test_chapter_parser_valid():
    raw_chapters = [
        {"start_time": 0, "end_time": 252.0, "title": "Separuh Aku"},
        {"start_time": 252.0, "end_time": 400.0, "title": "Tak Lagi Sama"},
        {"start_time": 400.0, "end_time": 600.0, "title": "Hidup Untukmu"},
    ]
    parser = ChapterParser()
    result = parser.parse(raw_chapters, total_duration=610)
    
    assert result.is_valid is True
    assert result.chapter_count == 3
    assert result.covers_full_duration is True
    assert len(result.tracks) == 3
    assert result.tracks[0].title == "Separuh Aku"
    assert result.tracks[0].source == "chapter"

def test_chapter_parser_invalid():
    raw_chapters = [
        {"start_time": 0, "end_time": 252.0, "title": "Separuh Aku"},
        {"start_time": 252.0, "end_time": 400.0, "title": "Tak Lagi Sama"},
    ]
    parser = ChapterParser()
    result = parser.parse(raw_chapters, total_duration=400)
    
    assert result.is_valid is False
    assert result.chapter_count == 2
    assert result.covers_full_duration is True # Ends exactly at total duration
    
def test_chapter_parser_empty():
    parser = ChapterParser()
    result = parser.parse(None, total_duration=100)
    assert result.is_valid is False
    assert result.chapter_count == 0

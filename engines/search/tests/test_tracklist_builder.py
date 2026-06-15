import pytest
from engines.search.metadata.chapter_parser import ChapterParseResult
from engines.search.metadata.timestamp_parser import TimestampParseResult
from engines.search.metadata.tracklist_builder import TracklistBuilder
from engines.search.models.track import Track

def test_tracklist_builder_prioritizes_chapters():
    chapter_res = ChapterParseResult(
        tracks=[Track("C1", 0), Track("C2", 1), Track("C3", 2)],
        chapter_count=3,
        covers_full_duration=True,
        is_valid=True
    )
    timestamp_res = TimestampParseResult(
        tracks=[Track("T1", 0), Track("T2", 1), Track("T3", 2)],
        timestamp_count=3,
        is_monotonic=True,
        is_valid=True
    )
    
    builder = TracklistBuilder()
    result = builder.build(chapter_res, timestamp_res)
    
    assert result.primary_source == "chapter"
    assert result.track_count == 3
    assert result.tracks[0].title == "C1"
    assert result.has_chapters is True
    assert result.has_timestamps is True

def test_tracklist_builder_uses_timestamps_if_no_chapters():
    timestamp_res = TimestampParseResult(
        tracks=[Track("T1", 0), Track("T2", 1), Track("T3", 2)],
        timestamp_count=3,
        is_monotonic=True,
        is_valid=True
    )
    
    builder = TracklistBuilder()
    result = builder.build(None, timestamp_res)
    
    assert result.primary_source == "timestamp"
    assert result.track_count == 3
    assert result.tracks[0].title == "T1"

def test_tracklist_builder_none():
    builder = TracklistBuilder()
    result = builder.build(None, None)
    
    assert result.primary_source == "none"
    assert result.track_count == 0

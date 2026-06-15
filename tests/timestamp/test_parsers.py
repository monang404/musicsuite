import pytest
from engines.timestamp.parsers.text_parser import parse_timestamps, time_to_seconds, seconds_to_time

def test_time_conversion():
    assert time_to_seconds("04:05") == 245
    assert time_to_seconds("01:12:30") == 4350
    assert seconds_to_time(245) == "04:05"
    assert seconds_to_time(4350) == "1:12:30"

def test_parse_timestamps():
    text = """
    00:00 | Intro
    03:15 | First Song
    07:30 | Second Song
    """
    tracks = parse_timestamps(text, audio_duration=600)
    
    assert len(tracks) == 3
    assert tracks[0].title == "Intro"
    assert tracks[0].start_seconds == 0
    assert tracks[0].end_seconds == 195
    
    assert tracks[1].title == "First Song"
    assert tracks[1].start_seconds == 195
    assert tracks[1].end_seconds == 450
    
    assert tracks[2].title == "Second Song"
    assert tracks[2].start_seconds == 450
    assert tracks[2].end_seconds == 600

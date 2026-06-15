import pytest
from engines.search.metadata.timestamp_parser import TimestampParser

def test_timestamp_parser_valid_standard():
    desc = """
    00:00 Intro
    03:22 Separuh Aku
    06:45 Tak Lagi Sama
    """
    parser = TimestampParser()
    result = parser.parse(desc)
    
    assert result.is_valid is True
    assert result.is_monotonic is True
    assert result.timestamp_count == 3
    assert result.tracks[0].title == "Intro"
    assert result.tracks[1].start_time == 202.0
    assert result.tracks[1].end_time == 405.0

def test_timestamp_parser_valid_numbered():
    desc = """
    1. 0:00 - First Song
    2. 3:00 - Second Song
    3. 6:00 - Third Song
    """
    parser = TimestampParser()
    result = parser.parse(desc)
    assert result.is_valid is True
    assert result.tracks[0].title == "First Song"

def test_timestamp_parser_bracketed():
    desc = """
    [00:00] First
    [03:00] Second
    [06:00] Third
    """
    parser = TimestampParser()
    result = parser.parse(desc)
    assert result.is_valid is True
    assert result.tracks[0].title == "First"

def test_timestamp_parser_non_monotonic():
    desc = """
    00:00 Song 1
    06:00 Song 2
    03:00 Song 3
    """
    parser = TimestampParser()
    result = parser.parse(desc)
    
    assert result.is_valid is True
    assert result.is_monotonic is False
    assert result.timestamp_count == 3

def test_timestamp_parser_empty():
    parser = TimestampParser()
    result = parser.parse("")
    assert result.is_valid is False
    assert result.timestamp_count == 0

def test_timestamp_parser_dot_separated():
    desc = """
    00.00 Intro
    03.22 Separuh Aku
    06.45 Tak Lagi Sama
    """
    parser = TimestampParser()
    result = parser.parse(desc)
    
    assert result.is_valid is True
    assert result.timestamp_count == 3
    assert result.tracks[1].start_time == 202.0

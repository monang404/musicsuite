import pytest
from engines.search.models.track import Track

def test_track_creation():
    t = Track(title="Intro", start_time=0.0)
    assert t.title == "Intro"
    assert t.start_time == 0.0
    assert t.end_time is None
    assert t.source == "unknown"

def test_track_duration():
    t = Track(title="Song", start_time=10.0, end_time=130.0)
    assert t.duration_seconds() == 120.0

def test_track_duration_no_end_time():
    t = Track(title="Song", start_time=10.0)
    assert t.duration_seconds() is None

def test_track_duration_invalid_end_time():
    t = Track(title="Song", start_time=10.0, end_time=5.0)
    assert t.duration_seconds() == 0.0  # max(0, -5)

def test_track_equality():
    t1 = Track(title="Song", start_time=10.0)
    t2 = Track(title="Song", start_time=10.0)
    t3 = Track(title="Song", start_time=15.0)
    assert t1 == t2
    assert t1 != t3

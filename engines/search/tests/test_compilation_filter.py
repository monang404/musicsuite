import pytest
from engines.search.ranking.compilation_filter import CompilationFilter
from engines.search.models.compilation_source import CompilationVideo

def test_filter_should_exclude():
    cf = CompilationFilter()
    assert cf.should_exclude("Coldplay Reaction Video") is True
    assert cf.should_exclude("Tutorial Gitar Noah") is True
    assert cf.should_exclude("Noah - Separuh Aku 10 hours") is True
    assert cf.should_exclude("Best Of NOAH") is False
    assert cf.should_exclude("NOAH Greatest Hits (Live Recording)") is False

def test_filter_compute_penalty():
    cf = CompilationFilter()
    assert cf.compute_penalty("Best Of NOAH") == 0
    assert cf.compute_penalty("NOAH Greatest Hits (Live Recording)") == 15
    assert cf.compute_penalty("Dewa 19 Slowed Reverb") == 40  # 20 + 20

def test_filter_apply():
    cf = CompilationFilter()
    s1 = CompilationVideo(id="1", url="", title="Best Of NOAH", channel="", duration=0, view_count=0, upload_date="")
    s2 = CompilationVideo(id="2", url="", title="Tutorial Gitar Noah", channel="", duration=0, view_count=0, upload_date="")
    s3 = CompilationVideo(id="3", url="", title="NOAH Live", channel="", duration=0, view_count=0, upload_date="")
    
    filtered = cf.apply([s1, s2, s3])
    
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[0].soft_penalty == 0
    assert filtered[1].id == "3"
    assert filtered[1].soft_penalty == 15

def test_filter_duration_pruning():
    cf = CompilationFilter()
    s1 = CompilationVideo(id="1", url="", title="Wali Full Album 2024", channel="", duration=3600, view_count=0, upload_date="")
    s2 = CompilationVideo(id="2", url="", title="Wali Full Album (Short Fake)", channel="", duration=300, view_count=0, upload_date="")
    s3 = CompilationVideo(id="3", url="", title="Wali Single", channel="", duration=300, view_count=0, upload_date="")
    
    filtered = cf.apply([s1, s2, s3])
    
    # s2 should be dropped because it's < 600s and claims to be an album
    # s3 should be kept because it's < 600s but doesn't claim to be an album
    assert len(filtered) == 2
    assert filtered[0].id == "1"
    assert filtered[1].id == "3"

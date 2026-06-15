import pytest
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.compilation_scorer import CompilationScorer
from engines.search.ranking.ranking import RankingEngine, RankedGroup

def test_scorer_chapter_score():
    scorer = CompilationScorer()
    # 18 valid chapters
    s = CompilationVideo(id="1", url="", title="", channel="", duration=300, view_count=0, upload_date="")
    s.has_chapters = True
    s.chapter_count = 18
    s.chapters_cover_full_duration = True
    assert scorer._chapter_score(s) == 45
    
    # 2 chapters (invalid)
    s.chapter_count = 2
    assert scorer._chapter_score(s) == 0

def test_scorer_timestamp_score():
    scorer = CompilationScorer()
    s = CompilationVideo(id="1", url="", title="", channel="", duration=300, view_count=0, upload_date="")
    s.has_timestamps = True
    s.timestamp_count = 12
    s.timestamps_are_monotonic = True
    assert scorer._timestamp_score(s) == 30

def test_scorer_compute_total_cap():
    scorer = CompilationScorer()
    components = {"a": 50, "b": 60}
    assert scorer._compute_total(components) == 100

def test_scorer_phase2_full():
    scorer = CompilationScorer("Noah")
    s = CompilationVideo(id="1", url="", title="Noah Greatest Hits", channel="Noah Official", duration=3000, view_count=0, upload_date="20250101")
    s.has_chapters = True
    s.chapter_count = 15
    s.chapters_cover_full_duration = True # 45
    s.track_count = 15 # 10
    # avg duration = 200s (between 150 and 360) # 8
    # Artist match # 5
    # Recency # 5
    
    res = scorer.score_phase2(s)
    assert res.score == 73 # 45 + 10 + 8 + 5 + 5
    assert res.is_estimate is False
    assert res.label == "Good"

def test_ranking_engine():
    re_engine = RankingEngine()
    s1 = CompilationVideo(id="1", url="", title="", channel="", duration=0, view_count=0, upload_date="20230101", track_count=10)
    s2 = CompilationVideo(id="2", url="", title="", channel="", duration=0, view_count=0, upload_date="20230101", track_count=20)
    s3 = CompilationVideo(id="3", url="", title="", channel="", duration=0, view_count=0, upload_date="20230101", track_count=10)
    
    qr = {
        "1": QualityResult(source_id="1", score=90, label="Excellent", is_estimate=False),
        "2": QualityResult(source_id="2", score=90, label="Excellent", is_estimate=False),
        "3": QualityResult(source_id="3", score=50, label="Fair", is_estimate=False)
    }
    
    groups = re_engine.rank([s1, s2, s3], qr)
    
    assert len(groups) == 2
    assert groups[0].label == "Excellent"
    assert groups[1].label == "Fair"
    
    # Check tiebreaker: s2 has more tracks than s1, so it should be first
    assert groups[0].sources[0].id == "2"
    assert groups[0].sources[1].id == "1"

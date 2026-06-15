import pytest
from engines.search.models.quality_result import QualityResult

def test_label_from_score():
    assert QualityResult.label_from_score(100) == "Excellent"
    assert QualityResult.label_from_score(90) == "Excellent"
    assert QualityResult.label_from_score(89) == "Very Good"
    assert QualityResult.label_from_score(75) == "Very Good"
    assert QualityResult.label_from_score(74) == "Good"
    assert QualityResult.label_from_score(55) == "Good"
    assert QualityResult.label_from_score(54) == "Fair"
    assert QualityResult.label_from_score(35) == "Fair"
    assert QualityResult.label_from_score(34) == "Poor"
    assert QualityResult.label_from_score(0) == "Poor"

def test_badge_color():
    res1 = QualityResult(source_id="1", score=95, label="Excellent", is_estimate=True)
    assert res1.badge_color == "#22C55E"
    
    res2 = QualityResult(source_id="2", score=40, label="Fair", is_estimate=False)
    assert res2.badge_color == "#F97316"

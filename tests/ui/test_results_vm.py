import pytest
from engines.search.models.compilation_source import CompilationVideo
from engines.search.ranking.ranking import RankedGroup
from engines.search.models.quality_result import QualityResult
from ui.viewmodels.results_vm import ResultsViewModel

@pytest.fixture
def sample_sources():
    s1 = CompilationVideo(id="1", url="http://1", title="Test 1", channel="Ch 1", duration=100, view_count=10, upload_date="2023", thumbnail_url="", track_count=0)
    s2 = CompilationVideo(id="2", url="http://2", title="Test 2", channel="Ch 2", duration=200, view_count=20, upload_date="2023", thumbnail_url="", track_count=0)
    return [s1, s2]

@pytest.fixture
def sample_payload(sample_sources):
    q1 = QualityResult(source_id="1", score=90, label="Excellent", is_estimate=True)
    q2 = QualityResult(source_id="2", score=80, label="Excellent", is_estimate=True)
    
    group = RankedGroup(label="Excellent", sources=sample_sources, quality_results={"1": q1, "2": q2})
    return {
        "compilations": [group],
        "playlists": []
    }

def test_results_vm_load_results(sample_payload):
    vm = ResultsViewModel()
    
    events = []
    vm.results_loaded.connect(lambda: events.append("loaded"))
    vm.state_changed.connect(lambda: events.append("state"))
    
    vm.load_results(sample_payload)
    
    assert len(vm.compilations) == 1
    assert len(vm.playlists) == 0
    assert "loaded" in events
    assert "state" in events

def test_results_vm_apply_filter():
    vm = ResultsViewModel()
    events = []
    vm.filter_applied.connect(lambda f: events.append(f))
    
    vm.apply_filter("test filter")
    
    assert vm.active_filter == "test filter"
    assert "test filter" in events

def test_results_vm_apply_sort():
    vm = ResultsViewModel()
    events = []
    vm.sort_applied.connect(lambda s: events.append(s))
    
    vm.apply_sort("Date")
    
    assert vm.active_sort == "Date"
    assert "Date" in events

def test_results_vm_select_source(sample_sources):
    vm = ResultsViewModel()
    events = []
    vm.source_selected.connect(lambda s: events.append(s))
    
    vm.select_source(sample_sources[0])
    
    assert vm.selected_source == sample_sources[0]
    assert sample_sources[0] in events

import pytest
from unittest.mock import MagicMock, patch
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.track import Track
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.ranking import RankedGroup
from ui.viewmodels.compilation_inspector_vm import CompilationInspectorViewModel


def _make_source(deep_fetched=False, tracks=None):
    """Helper to create a test CompilationVideo object."""
    s = CompilationVideo(
        id="abc12345",
        url="https://youtube.com/watch?v=test",
        title="Test Album - Full Album",
        channel="Test Channel",
        duration=3600,
        view_count=100000,
        upload_date="20240101",
        thumbnail_url="https://img.youtube.com/thumb.jpg",
        track_count=len(tracks) if tracks else 0,
        has_chapters=bool(tracks),
        has_timestamps=bool(tracks),
        chapters_cover_full_duration=bool(tracks),
        timestamps_are_monotonic=True,
        is_deep_fetched=deep_fetched,
        tracks=tracks or [],
    )
    return s


def _make_tracks(n=5):
    """Helper to create a list of test Track objects."""
    tracks = []
    for i in range(n):
        tracks.append(Track(
            title=f"Track {i + 1}",
            start_time=float(i * 300),
            end_time=float((i + 1) * 300) if i < n - 1 else None,
            source="chapter",
        ))
    return tracks


@pytest.fixture(autouse=True)
def mock_worker_sync():
    """Monkeypatches CompilationInspectorWorker.start to run synchronously for VM tests."""
    from ui.workers.compilation_inspector_worker import CompilationInspectorWorker
    original_start = CompilationInspectorWorker.start

    def run_sync(self):
        self.run()

    CompilationInspectorWorker.start = run_sync
    yield
    CompilationInspectorWorker.start = original_start


@pytest.fixture
def mock_services():
    """Patches ServiceContainer to use mock services."""
    mock_search = MagicMock()
    mock_timestamp = MagicMock()

    with patch("ui.workers.compilation_inspector_worker.ServiceContainer") as MockContainer:
        instance = MockContainer.return_value
        instance.search_service = mock_search
        instance.timestamp_service = mock_timestamp
        yield mock_search, mock_timestamp


def test_load_source_deep_fetched(mock_services):
    """Loading an already deep-fetched source should skip fetching."""
    mock_search, _ = mock_services

    tracks = _make_tracks(3)
    source = _make_source(deep_fetched=True, tracks=tracks)

    # Mock rank_results to return a scored group
    quality = QualityResult(source_id="abc12345", score=85, label="Great", is_estimate=False)
    group = RankedGroup(label="Great", sources=[source], quality_results={"abc12345": quality})
    mock_search.rank_results.return_value = [group]

    vm = CompilationInspectorViewModel()

    events = []
    vm.analysis_completed.connect(lambda: events.append("completed"))
    vm.state_changed.connect(lambda: events.append("state"))

    vm.load_source(source)

    # Should NOT have called fetch_metadata since already deep-fetched
    mock_search.fetch_metadata.assert_not_called()

    assert vm.source == source
    assert vm.analysis_status == "ready"
    assert len(vm.tracks) == 3
    assert vm.confidence_score is not None
    assert vm.confidence_score.score == 85
    assert "completed" in events
    assert vm.metadata["title"] == "Test Album - Full Album"
    assert vm.metadata["channel"] == "Test Channel"
    assert vm.metadata["track_count"] == 3


def test_load_source_needs_fetch(mock_services):
    """Loading a non-deep-fetched source should trigger fetch_metadata."""
    mock_search, _ = mock_services

    source = _make_source(deep_fetched=False)
    fetched_source = _make_source(deep_fetched=True, tracks=_make_tracks(5))
    mock_search.fetch_metadata.return_value = fetched_source

    quality = QualityResult(source_id="abc12345", score=72, label="Poor", is_estimate=False)
    group = RankedGroup(label="Poor", sources=[fetched_source], quality_results={"abc12345": quality})
    mock_search.rank_results.return_value = [group]

    vm = CompilationInspectorViewModel()

    events = []
    vm.analysis_completed.connect(lambda: events.append("completed"))

    vm.load_source(source)

    mock_search.fetch_metadata.assert_called_once_with(source.url)
    assert vm.source.is_deep_fetched is True
    assert vm.analysis_status == "ready"
    assert len(vm.tracks) == 5
    assert "completed" in events


def test_load_source_fetch_fails(mock_services):
    """If fetch_metadata raises, analysis should fail gracefully."""
    mock_search, _ = mock_services

    source = _make_source(deep_fetched=False)
    mock_search.fetch_metadata.side_effect = RuntimeError("Network error")

    vm = CompilationInspectorViewModel()

    errors = []
    vm.analysis_failed.connect(lambda e: errors.append(e))

    vm.load_source(source)

    assert vm.analysis_status == "failed"
    assert len(errors) == 1
    assert "Network error" in errors[0]
    assert vm.error_message == "Network error"


def test_confidence_score_calculation(mock_services):
    """Confidence score should be derived from rank_results."""
    mock_search, _ = mock_services

    tracks = _make_tracks(10)
    source = _make_source(deep_fetched=True, tracks=tracks)

    quality = QualityResult(source_id="abc12345", score=96, label="Excellent", is_estimate=False)
    group = RankedGroup(label="Excellent", sources=[source], quality_results={"abc12345": quality})
    mock_search.rank_results.return_value = [group]

    vm = CompilationInspectorViewModel()
    vm.load_source(source)

    assert vm.confidence_score is not None
    assert vm.confidence_score.score == 96
    assert vm.confidence_score.label == "Excellent"


def test_update_timestamps_parses_tracks(mock_services):
    """update_timestamps should parse MM:SS|Title format into Track objects."""
    mock_search, _ = mock_services

    tracks = _make_tracks(2)
    source = _make_source(deep_fetched=True, tracks=tracks)
    mock_search.rank_results.return_value = []

    vm = CompilationInspectorViewModel()
    vm.load_source(source)

    # Manually update timestamps
    new_text = "00:00|Intro\n03:45|Verse 1\n07:30|Chorus"
    vm.update_timestamps(new_text)

    assert len(vm.tracks) == 3
    assert vm.tracks[0].title == "Intro"
    assert vm.tracks[0].start_time == 0.0
    assert vm.tracks[1].title == "Verse 1"
    assert vm.tracks[1].start_time == 225.0  # 3*60 + 45
    assert vm.tracks[2].title == "Chorus"
    assert vm.tracks[2].start_time == 450.0  # 7*60 + 30

    # End times should be calculated
    assert vm.tracks[0].end_time == 225.0
    assert vm.tracks[1].end_time == 450.0
    assert vm.tracks[2].end_time is None


def test_metadata_duration_statistics(mock_services):
    """Metadata should include duration statistics."""
    mock_search, _ = mock_services

    tracks = _make_tracks(10)  # 10 tracks across 3600s = 360s avg
    source = _make_source(deep_fetched=True, tracks=tracks)

    mock_search.rank_results.return_value = []

    vm = CompilationInspectorViewModel()
    vm.load_source(source)

    assert vm.metadata["duration"] == 3600
    assert vm.metadata["duration_formatted"] == "1:00:00"
    assert vm.metadata["track_count"] == 10
    assert vm.metadata["avg_track_duration"] == 360.0
    assert vm.metadata["avg_track_duration_formatted"] == "06:00"


def test_timestamp_text_generation(mock_services):
    """Loading a source with tracks should generate timestamp text."""
    mock_search, _ = mock_services

    tracks = [
        Track(title="Song A", start_time=0.0, end_time=180.0, source="chapter"),
        Track(title="Song B", start_time=180.0, end_time=360.0, source="chapter"),
    ]
    source = _make_source(deep_fetched=True, tracks=tracks)

    mock_search.rank_results.return_value = []

    vm = CompilationInspectorViewModel()
    vm.load_source(source)

    assert "00:00|Song A" in vm.timestamps
    assert "03:00|Song B" in vm.timestamps


def test_empty_source_tracks(mock_services):
    """A source with no tracks should have empty tracks and timestamps."""
    mock_search, _ = mock_services

    source = _make_source(deep_fetched=True, tracks=[])
    mock_search.rank_results.return_value = []

    vm = CompilationInspectorViewModel()
    vm.load_source(source)

    assert vm.tracks == []
    assert vm.timestamps == ""
    assert vm.metadata["track_count"] == 0
    assert vm.metadata["avg_track_duration_formatted"] == "N/A"


def test_format_duration():
    """Test the static duration formatter."""
    assert CompilationInspectorViewModel._format_duration(0) == "00:00"
    assert CompilationInspectorViewModel._format_duration(65) == "01:05"
    assert CompilationInspectorViewModel._format_duration(3661) == "1:01:01"
    assert CompilationInspectorViewModel._format_duration(7200) == "2:00:00"

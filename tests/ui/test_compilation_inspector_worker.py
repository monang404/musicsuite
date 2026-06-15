import pytest
from unittest.mock import MagicMock, patch
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.track import Track
from engines.search.models.quality_result import QualityResult
from engines.search.ranking.ranking import RankedGroup
from ui.workers.compilation_inspector_worker import CompilationInspectorWorker


def _make_source(deep_fetched=False, tracks=None):
    return CompilationVideo(
        id="abc12345",
        url="https://youtube.com/watch?v=test",
        title="Test Album",
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


@pytest.fixture
def mock_search_service():
    with patch("ui.workers.compilation_inspector_worker.ServiceContainer") as MockContainer:
        instance = MockContainer.return_value
        mock_search = MagicMock()
        instance.search_service = mock_search
        yield mock_search


def test_worker_execute_deep_fetched(mock_search_service):
    """If source is already deep-fetched, the worker skips fetching and runs ranking."""
    source = _make_source(deep_fetched=True, tracks=[])
    
    quality = QualityResult(source_id="abc12345", score=85, label="Great", is_estimate=False)
    group = RankedGroup(label="Great", sources=[source], quality_results={"abc12345": quality})
    mock_search_service.rank_results.return_value = [group]

    worker = CompilationInspectorWorker(source)
    
    completed_payload = None
    def on_completed(payload):
        nonlocal completed_payload
        completed_payload = payload

    worker.completed.connect(on_completed)
    worker._execute_work()

    mock_search_service.fetch_metadata.assert_not_called()
    mock_search_service.rank_results.assert_called_once_with([source])
    
    assert completed_payload is not None
    assert completed_payload["source"] == source
    assert completed_payload["confidence_score"] == quality
    assert completed_payload["metadata"]["title"] == "Test Album"


def test_worker_execute_needs_fetch(mock_search_service):
    """If source is not deep-fetched, the worker fetches metadata first."""
    source = _make_source(deep_fetched=False)
    fetched_source = _make_source(deep_fetched=True)
    
    mock_search_service.fetch_metadata.return_value = fetched_source
    mock_search_service.rank_results.return_value = []

    worker = CompilationInspectorWorker(source)
    
    completed_payload = None
    def on_completed(payload):
        nonlocal completed_payload
        completed_payload = payload

    worker.completed.connect(on_completed)
    worker._execute_work()

    mock_search_service.fetch_metadata.assert_called_once_with(source.url)
    assert completed_payload is not None
    assert completed_payload["source"] == fetched_source


def test_worker_cancellation(mock_search_service):
    """If cancelled is requested, the worker emits cancelled and exits early."""
    source = _make_source(deep_fetched=True)
    
    worker = CompilationInspectorWorker(source)
    worker.cancel()  # Request cancellation

    cancelled_emitted = False
    def on_cancelled():
        nonlocal cancelled_emitted
        cancelled_emitted = True

    worker.cancelled.connect(on_cancelled)
    worker._execute_work()

    mock_search_service.rank_results.assert_not_called()
    assert cancelled_emitted is True

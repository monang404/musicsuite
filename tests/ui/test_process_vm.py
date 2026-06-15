import pytest
from unittest.mock import MagicMock, patch
from engines.search.models.compilation_source import CompilationVideo
from ui.viewmodels.process_vm import ProcessViewModel, WorkflowJob


def _make_source():
    return CompilationVideo(
        id="abc12345",
        url="https://youtube.com/watch?v=test",
        title="Test Album - Full Album",
        channel="Test Channel",
        duration=3600,
        view_count=100000,
        upload_date="20240101",
        thumbnail_url="https://img.youtube.com/thumb.jpg",
        track_count=0,
    )


@pytest.fixture
def mock_container():
    """Patches ServiceContainer to mock services."""
    mock_workflow = MagicMock()
    with patch("ui.viewmodels.process_vm.ServiceContainer") as MockContainer:
        instance = MockContainer.return_value
        instance.workflow_service = mock_workflow
        yield mock_workflow


def test_initial_state(mock_container):
    vm = ProcessViewModel()
    assert vm.source is None
    assert vm.timestamps == ""
    assert vm.metadata == {}
    assert vm.output_folder == ""
    assert vm.audio_format == "mp3"
    assert vm.bitrate == "320k"
    assert vm.naming_pattern == "{index:03d} - {title}"
    assert vm.export_options["split_audio"] is True
    assert vm.export_options["write_tags"] is True
    assert vm.export_options["embed_thumbnail"] is False
    assert vm.export_options["create_playlist"] is False


def test_load_source(mock_container):
    vm = ProcessViewModel()
    source = _make_source()
    timestamps = "00:00|Intro\n05:00|Track 1"
    metadata = {"key": "val"}

    events = []
    vm.state_changed.connect(lambda: events.append("changed"))

    vm.load_source(source, timestamps, metadata)

    assert vm.source == source
    assert vm.timestamps == timestamps
    assert vm.metadata == metadata
    assert "changed" in events


def test_setters(mock_container):
    vm = ProcessViewModel()
    events = []
    vm.state_changed.connect(lambda: events.append("changed"))

    vm.set_output_folder("/path/to/output")
    vm.set_audio_format("flac")
    vm.set_bitrate("256k")
    vm.set_naming_pattern("{title}")
    vm.set_export_option("embed_thumbnail", True)

    assert vm.output_folder == "/path/to/output"
    assert vm.audio_format == "flac"
    assert vm.bitrate == "256k"
    assert vm.naming_pattern == "{title}"
    assert vm.export_options["embed_thumbnail"] is True
    assert len(events) == 5



def test_validation_fails_when_missing_format(mock_container):
    vm = ProcessViewModel()
    vm.set_output_folder("/output")
    vm.set_audio_format("")
    is_valid, errors = vm.validate()
    assert is_valid is False
    assert "Audio format is required." in errors


def test_validation_fails_when_missing_bitrate(mock_container):
    vm = ProcessViewModel()
    vm.set_output_folder("/output")
    vm.set_bitrate("")
    is_valid, errors = vm.validate()
    assert is_valid is False
    assert "Bitrate is required." in errors


@patch("os.makedirs")
def test_start_job_success(mock_makedirs, mock_container):
    vm = ProcessViewModel()
    source = _make_source()
    
    with patch("ui.core.app_settings.AppSettings.get_default_folder", return_value="/default"):
        vm.load_source(source, "00:00|Intro", {"channel": "Test Channel"})

    job_events = []
    vm.job_configured.connect(lambda j: job_events.append(j))

    job = vm.start_job()

    assert job is not None
    assert isinstance(job, WorkflowJob)
    assert job.source == source
    assert job.timestamps == "00:00|Intro"
    import os
    assert job.output_folder == os.path.join("/default", "kompilasi", "Test Compilation")
    assert job.audio_format == "mp3"
    assert job.bitrate == "320k"
    
    assert len(job_events) == 1
    assert job_events[0] == job
    mock_makedirs.assert_called_once_with(job.output_folder, exist_ok=True)


def test_start_job_validation_error(mock_container):
    vm = ProcessViewModel()
    vm.set_audio_format("")  # Invalid

    errors = []
    vm.error_occurred.connect(lambda e: errors.append(e))

    job = vm.start_job()

    assert job is None
    assert len(errors) == 1
    assert "Audio format is required." in errors[0]

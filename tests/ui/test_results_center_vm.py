import pytest
from unittest.mock import MagicMock, patch


FAKE_HISTORY = [
    {
        "id": "job-1",
        "title": "Dark Side of the Moon",
        "source_type": "playlist",
        "status": "COMPLETED",
        "completed_at": "2026-06-11T06:00:00",
        "result_files": ["/out/track1.mp3", "/out/track2.mp3"],
        "error_message": None,
        "metadata": {},
    },
    {
        "id": "job-2",
        "title": "Abbey Road",
        "source_type": "compilation",
        "status": "FAILED",
        "completed_at": "2026-06-11T07:00:00",
        "result_files": [],
        "error_message": "Download timed out",
        "metadata": {},
    },
    {
        "id": "job-3",
        "title": "Led Zeppelin IV",
        "source_type": "playlist",
        "status": "COMPLETED",
        "completed_at": "2026-06-11T08:00:00",
        "result_files": ["/out/zep1.mp3"],
        "error_message": None,
        "metadata": {},
    },
]


@pytest.fixture
def mock_container():
    with patch("ui.viewmodels.results_center_vm.ServiceContainer") as mock_cls:
        mock_c = MagicMock()
        mock_store = MagicMock()
        mock_store.retrieve_history.return_value = FAKE_HISTORY[:]
        mock_c.result_store = mock_store
        mock_cls.return_value = mock_c
        yield mock_c


@pytest.fixture
def vm(mock_container):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    viewmodel = ResultsCenterViewModel()
    viewmodel.load_history()
    return viewmodel


# ── Initial state ───────────────────────────────────────────────────────────

def test_initial_filter_is_all(vm):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    assert vm.active_filter == ResultsCenterViewModel.FILTER_ALL


def test_initial_search_empty(vm):
    assert vm.search_query == ""


# ── Completed / failed properties ───────────────────────────────────────────

def test_completed_jobs(vm):
    assert len(vm.completed_jobs) == 2
    assert all(j["status"] == "COMPLETED" for j in vm.completed_jobs)


def test_failed_jobs(vm):
    assert len(vm.failed_jobs) == 1
    assert vm.failed_jobs[0]["id"] == "job-2"


# ── Derived properties ──────────────────────────────────────────────────────

def test_exported_tracks(vm):
    # job-1 has 2 tracks, job-3 has 1
    assert len(vm.exported_tracks) == 3


def test_output_folders_unique(vm):
    # Both completed jobs write to /out — only one unique folder
    folders = vm.output_folders
    assert len(folders) == 1
    assert "out" in folders[0]


# ── Filtering ───────────────────────────────────────────────────────────────

def test_filter_completed(vm):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    vm.set_filter(ResultsCenterViewModel.FILTER_COMPLETED)
    visible = vm.visible_records
    assert all(r["status"] == "COMPLETED" for r in visible)
    assert len(visible) == 2


def test_filter_failed(vm):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    vm.set_filter(ResultsCenterViewModel.FILTER_FAILED)
    visible = vm.visible_records
    assert all(r["status"] == "FAILED" for r in visible)
    assert len(visible) == 1


def test_filter_all(vm):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    vm.set_filter(ResultsCenterViewModel.FILTER_COMPLETED)
    vm.set_filter(ResultsCenterViewModel.FILTER_ALL)
    assert len(vm.visible_records) == 3


def test_unknown_filter_emits_error(vm):
    errors = []
    vm.error_occurred.connect(lambda msg: errors.append(msg))
    vm.set_filter("UNKNOWN")
    assert len(errors) == 1
    assert "Unknown filter" in errors[0]


# ── Search ──────────────────────────────────────────────────────────────────

def test_search_by_title(vm):
    vm.set_search_query("abbey")
    assert len(vm.visible_records) == 1
    assert vm.visible_records[0]["id"] == "job-2"


def test_search_by_source_type(vm):
    vm.set_search_query("compilation")
    assert len(vm.visible_records) == 1
    assert vm.visible_records[0]["source_type"] == "compilation"


def test_search_no_match(vm):
    vm.set_search_query("zzznomatch")
    assert len(vm.visible_records) == 0


def test_search_combined_with_filter(vm):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    vm.set_filter(ResultsCenterViewModel.FILTER_COMPLETED)
    vm.set_search_query("zeppelin")
    assert len(vm.visible_records) == 1
    assert vm.visible_records[0]["id"] == "job-3"


# ── Delete ──────────────────────────────────────────────────────────────────

def test_delete_removes_record(vm, mock_container):
    vm.delete_record("job-2")
    mock_container.result_store.delete_record.assert_called_once_with("job-2")
    assert all(r["id"] != "job-2" for r in vm.visible_records)


# ── Load error handling ─────────────────────────────────────────────────────

def test_load_history_error_emits_signal(mock_container):
    from ui.viewmodels.results_center_vm import ResultsCenterViewModel
    mock_container.result_store.retrieve_history.side_effect = RuntimeError("DB error")
    vm = ResultsCenterViewModel()
    errors = []
    vm.error_occurred.connect(lambda m: errors.append(m))
    vm.load_history()
    assert any("Failed to load history" in e for e in errors)
    assert vm.visible_records == []

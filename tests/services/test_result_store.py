import pytest
import sqlite3
import json
from pathlib import Path
from services.result_store import ResultStore

@pytest.fixture
def store(tmp_path):
    db_path = tmp_path / "test.db"
    return ResultStore(db_path=db_path)

def test_store_completed(store):
    store.store_completed(
        job_id="job123",
        title="Test Compilation",
        source_type="compilation",
        result_files=["file1.mp3", "file2.mp3"],
        metadata={"quality": "320k"}
    )
    
    history = store.retrieve_history()
    assert len(history) == 1
    assert history[0]["id"] == "job123"
    assert history[0]["status"] == "COMPLETED"
    assert history[0]["result_files"] == ["file1.mp3", "file2.mp3"]
    assert history[0]["metadata"] == {"quality": "320k"}

def test_store_failed(store):
    store.store_failed(
        job_id="job456",
        title="Test Failed Job",
        source_type="playlist",
        error_message="Network Error"
    )
    
    history = store.retrieve_history()
    assert len(history) == 1
    assert history[0]["id"] == "job456"
    assert history[0]["status"] == "FAILED"
    assert history[0]["error_message"] == "Network Error"
    assert history[0]["result_files"] == []

def test_delete_record(store):
    store.store_completed("job1", "Title 1", "compilation", [])
    store.store_completed("job2", "Title 2", "compilation", [])
    
    history = store.retrieve_history()
    assert len(history) == 2
    
    store.delete_record("job1")
    history = store.retrieve_history()
    assert len(history) == 1
    assert history[0]["id"] == "job2"

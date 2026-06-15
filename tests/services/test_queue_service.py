import pytest
from services.queue_service import QueueService, JobStatus

@pytest.fixture
def queue():
    return QueueService()

def test_add_job(queue):
    events = []
    queue.add_listener(lambda event, payload: events.append((event, payload)))
    
    job_id = queue.add_job({"url": "http://example.com"})
    
    assert len(queue.get_all_jobs()) == 1
    job = queue.get_job(job_id)
    assert job.status == JobStatus.PENDING
    assert job.params == {"url": "http://example.com"}
    
    assert len(events) == 1
    assert events[0][0] == "JOB_ADDED"
    assert events[0][1]["job_id"] == job_id

def test_job_controls(queue):
    job_id = queue.add_job({"url": "http://example.com"})
    
    queue.pause_job(job_id)
    assert queue.get_job(job_id).status == JobStatus.PAUSED
    
    queue.resume_job(job_id)
    assert queue.get_job(job_id).status == JobStatus.PENDING
    
    queue.cancel_job(job_id)
    assert queue.get_job(job_id).status == JobStatus.CANCELLED

def test_track_status(queue):
    events = []
    queue.add_listener(lambda event, payload: events.append(event))
    
    job_id = queue.add_job({})
    queue.track_status(job_id, JobStatus.RUNNING, progress=50, message="Downloading")
    
    job = queue.get_job(job_id)
    assert job.status == JobStatus.RUNNING
    assert job.progress == 50
    assert job.status_message == "Downloading"
    assert "JOB_STATUS_CHANGED" in events

def test_remove_job(queue):
    job_id = queue.add_job({})
    queue.remove_job(job_id)
    assert queue.get_job(job_id) is None
    assert len(queue.get_all_jobs()) == 0

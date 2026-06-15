import pytest
from unittest.mock import MagicMock, patch
from ui.viewmodels.queue_vm import QueueViewModel
from ui.viewmodels.process_vm import WorkflowJob
from services.queue_service import JobStatus, Job

@pytest.fixture
def mock_service_container():
    with patch("ui.viewmodels.queue_vm.ServiceContainer") as mock_container_cls:
        mock_container = MagicMock()
        mock_queue_service = MagicMock()
        
        # We need a bit more realistic queue service mock to test concurrency
        jobs = {}
        def mock_add_job(params):
            job_id = f"job-{len(jobs)+1}"
            jobs[job_id] = Job(id=job_id, params=params)
            return job_id
            
        def mock_get_all_jobs():
            return list(jobs.values())
            
        def mock_track_status(job_id, status, **kwargs):
            if job_id in jobs:
                jobs[job_id].status = status
                
        def mock_get_job(job_id):
            return jobs.get(job_id)
            
        mock_queue_service.add_job.side_effect = mock_add_job
        mock_queue_service.get_all_jobs.side_effect = mock_get_all_jobs
        mock_queue_service.track_status.side_effect = mock_track_status
        mock_queue_service.get_job.side_effect = mock_get_job
        
        mock_container.queue_service = mock_queue_service
        mock_container_cls.return_value = mock_container
        yield mock_container

@pytest.fixture
def mock_workflow_worker():
    with patch("ui.viewmodels.queue_vm.WorkflowWorker") as mock_worker_cls:
        mock_worker_cls.side_effect = lambda **kwargs: MagicMock()
        yield mock_worker_cls

def test_initial_state(mock_service_container):
    vm = QueueViewModel()
    assert vm.max_concurrent_jobs == 3
    assert len(vm.active_jobs) == 0

def test_add_workflow_job_starts_worker(mock_service_container, mock_workflow_worker):
    vm = QueueViewModel()
    job_dto = MagicMock(spec=WorkflowJob)
    job_dto.source = MagicMock()
    job_dto.output_folder = "/path"
    job_dto.audio_format = "mp3"
    
    vm.add_workflow_job(job_dto)
    
    assert mock_workflow_worker.call_count == 1
    assert len(vm._workers) == 1
    assert vm.all_jobs[0].status == JobStatus.RUNNING

def test_concurrency_limit(mock_service_container, mock_workflow_worker):
    vm = QueueViewModel()
    vm.max_concurrent_jobs = 2
    
    # Add 4 jobs
    for i in range(4):
        job_dto = MagicMock(spec=WorkflowJob)
        job_dto.source = MagicMock()
        job_dto.output_folder = "/path"
        job_dto.audio_format = "mp3"
        vm.add_workflow_job(job_dto)
    
    # Only 2 workers should be created
    assert mock_workflow_worker.call_count == 2
    assert len(vm._workers) == 2
    
    # 2 jobs running, 2 jobs pending
    statuses = [j.status for j in vm.all_jobs]
    assert statuses.count(JobStatus.RUNNING) == 2
    assert statuses.count(JobStatus.PENDING) == 2

def test_auto_start_next_job_on_completion(mock_service_container, mock_workflow_worker):
    vm = QueueViewModel()
    vm.max_concurrent_jobs = 1
    
    # Add 2 jobs
    for i in range(2):
        job_dto = MagicMock(spec=WorkflowJob)
        job_dto.source = MagicMock()
        job_dto.output_folder = "/path"
        job_dto.audio_format = "mp3"
        vm.add_workflow_job(job_dto)
        
    assert mock_workflow_worker.call_count == 1
    
    # Simulate completion of first job
    first_job_id = vm.all_jobs[0].id
    vm._on_worker_completed(first_job_id, [])
    
    # The second job should now start
    assert mock_workflow_worker.call_count == 2
    assert len(vm._workers) == 1
    
def test_retry_job_obeys_concurrency(mock_service_container, mock_workflow_worker):
    vm = QueueViewModel()
    vm.max_concurrent_jobs = 1
    
    job_dto = MagicMock(spec=WorkflowJob)
    job_dto.source = MagicMock()
    job_dto.output_folder = "/path"
    job_dto.audio_format = "mp3"
    
    vm.add_workflow_job(job_dto)
    assert mock_workflow_worker.call_count == 1
    
    # Fail it
    first_job_id = vm.all_jobs[0].id
    vm._on_worker_failed(first_job_id, "Error")
    
    # Add another job which takes up the slot
    vm.add_workflow_job(job_dto)
    assert mock_workflow_worker.call_count == 2
    
    # Retry first job. Should stay pending.
    vm.retry_job(first_job_id)
    assert mock_workflow_worker.call_count == 2
    assert vm.all_jobs[0].status == JobStatus.PENDING

from typing import Dict, List, Optional
from PySide6.QtCore import Signal
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.core.service_container import ServiceContainer
from ui.viewmodels.process_vm import WorkflowJob
from ui.workers.workflow_worker import WorkflowWorker
from services.queue_service import Job, JobStatus

class QueueViewModel(BaseViewModel):
    """
    ViewModel for the Queue Screen.
    Manages active, queued, completed, and failed jobs.
    Controls the lifecycle of WorkflowWorkers and delegates to QueueService.
    Implements worker pool architecture for controlled concurrency.
    """
    
    # Emitted when the queue lists change
    queue_updated = Signal()
    
    job_started = Signal(str)        # job_id
    job_progress = Signal(str, float) # message, pct
    job_completed = Signal(list)     # result_files
    job_failed = Signal(str)         # error message
    job_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        container = ServiceContainer()
        self._queue_service = container.queue_service
        
        # Concurrency Model
        self.max_concurrent_jobs: int = 3
        
        # Listen to QueueService events
        self._queue_service.add_listener(self._on_queue_event)
        
        self._workers: Dict[str, WorkflowWorker] = {}
        
    def _on_queue_event(self, event_type: str, payload: dict):
        # When queue service updates, notify UI
        self.queue_updated.emit()
        
    @property
    def all_jobs(self) -> List[Job]:
        return self._queue_service.get_all_jobs()
        
    @property
    def queued_jobs(self) -> List[Job]:
        return [j for j in self.all_jobs if j.status == JobStatus.PENDING]
        
    @property
    def active_jobs(self) -> List[Job]:
        return [j for j in self.all_jobs if j.status in (JobStatus.RUNNING, JobStatus.PAUSED)]
        
    @property
    def completed_jobs(self) -> List[Job]:
        return [j for j in self.all_jobs if j.status == JobStatus.COMPLETED]
        
    @property
    def failed_jobs(self) -> List[Job]:
        return [j for j in self.all_jobs if j.status in (JobStatus.FAILED, JobStatus.CANCELLED)]

    def add_workflow_job(self, job_dto: WorkflowJob):
        """Called when navigated from PROCESS with a new job."""
        params = {
            "source": job_dto.source,
            "output_folder": job_dto.output_folder,
            "format": job_dto.audio_format,
            "workflow_dto": job_dto  # Keep reference to the DTO
        }
        self._queue_service.add_job(params)
        self._process_pending_jobs()

    def _process_pending_jobs(self):
        """Worker pool logic to start pending jobs if capacity allows."""
        while len(self._workers) < self.max_concurrent_jobs:
            pending = self.queued_jobs
            if not pending:
                break
                
            next_job = None
            for job in pending:
                if job.id not in self._workers:
                    next_job = job
                    break
                    
            if not next_job:
                break
                
            if "workflow_dto" in next_job.params:
                # Mark as running immediately to prevent race conditions in loop
                self._queue_service.track_status(next_job.id, JobStatus.RUNNING, message="Starting...")
                self._start_worker(next_job.id, next_job.params["workflow_dto"])
            else:
                self._queue_service.track_status(next_job.id, JobStatus.FAILED, message="Missing DTO")

    def _start_worker(self, job_id: str, job_dto: WorkflowJob):
        worker = WorkflowWorker(job_id=job_id, job_dto=job_dto, parent=self)
        
        # Connect signals
        worker.started.connect(lambda: self._on_worker_started(job_id))
        worker.progress.connect(lambda msg, pct: self._on_worker_progress(job_id, msg, pct))
        worker.completed.connect(lambda res: self._on_worker_completed(job_id, res))
        worker.failed.connect(lambda err: self._on_worker_failed(job_id, err))
        worker.cancelled.connect(lambda: self._on_worker_cancelled(job_id))
        
        self._workers[job_id] = worker
        worker.start()
        
    def _on_worker_started(self, job_id: str):
        self._queue_service.track_status(job_id, JobStatus.RUNNING, message="Running")
        self.job_started.emit(job_id)
        
    def _on_worker_progress(self, job_id: str, msg: str, pct: float):
        self._queue_service.track_status(job_id, JobStatus.RUNNING, message=msg)
        self.job_progress.emit(msg, pct)
        
    def _on_worker_completed(self, job_id: str, results: list):
        self._queue_service.track_status(job_id, JobStatus.COMPLETED, message="Complete")
        
        job = self._queue_service.get_job(job_id)
        if job and "workflow_dto" in job.params:
            dto = job.params["workflow_dto"]
            source = getattr(dto, "source", None)
            title = getattr(source, "title", "Unknown") if source else "Unknown"
            entity_type = getattr(source, "entity_type", "unknown") if source else "unknown"
            
            meta_attr = getattr(dto, "metadata", {})
            meta = meta_attr.copy() if meta_attr else {}
            meta["output_folder"] = getattr(dto, "output_folder", "")
            
            ServiceContainer().result_store.store_completed(
                job_id=job_id, title=title, source_type=entity_type,
                result_files=results, metadata=meta
            )
            
        if job_id in self._workers:
            del self._workers[job_id]
        self._process_pending_jobs()
        self.job_completed.emit(results)
            
    def _on_worker_failed(self, job_id: str, err: str):
        self._queue_service.track_status(job_id, JobStatus.FAILED, message="Failed", error=err)
        
        job = self._queue_service.get_job(job_id)
        if job and "workflow_dto" in job.params:
            dto = job.params["workflow_dto"]
            source = getattr(dto, "source", None)
            title = getattr(source, "title", "Unknown") if source else "Unknown"
            entity_type = getattr(source, "entity_type", "unknown") if source else "unknown"
            
            meta_attr = getattr(dto, "metadata", {})
            meta = meta_attr.copy() if meta_attr else {}
            meta["output_folder"] = getattr(dto, "output_folder", "")
            
            ServiceContainer().result_store.store_failed(
                job_id=job_id, title=title, source_type=entity_type,
                error_message=err, metadata=meta
            )
            
        if job_id in self._workers:
            del self._workers[job_id]
        self._process_pending_jobs()
        self.job_failed.emit(err)
            
    def _on_worker_cancelled(self, job_id: str):
        self._queue_service.track_status(job_id, JobStatus.CANCELLED, message="Cancelled")
        if job_id in self._workers:
            del self._workers[job_id]
        self._process_pending_jobs()
        self.job_cancelled.emit()

    def pause_job(self, job_id: str):
        self._queue_service.pause_job(job_id)
        # Note: Worker cannot easily be paused due to ffmpeg subprocesses, but we mark state.
        
    def resume_job(self, job_id: str):
        self._queue_service.resume_job(job_id)

    def cancel_job(self, job_id: str):
        self._queue_service.cancel_job(job_id)
        if job_id in self._workers:
            self._workers[job_id].cancel()

    def retry_job(self, job_id: str):
        job = self._queue_service.get_job(job_id)
        if job and job.status in (JobStatus.FAILED, JobStatus.CANCELLED):
            self._queue_service.track_status(job_id, JobStatus.PENDING, message="Waiting...")
            self._process_pending_jobs()

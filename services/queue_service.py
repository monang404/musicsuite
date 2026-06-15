import uuid
from typing import Callable, Dict, Any, List, Optional
from enum import Enum

class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Job:
    """Represents a single task in the queue."""
    def __init__(self, id: str, params: Dict[str, Any]):
        self.id = id
        self.params = params
        self.status = JobStatus.PENDING
        self.progress = 0
        self.status_message = "Waiting..."
        self.error_message = None

class QueueService:
    """Service for managing background jobs, tracking their statuses, and emitting events."""
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        # List of callables that receive an event type (str) and payload (Any)
        self._listeners: List[Callable[[str, Any], None]] = []
        
    def add_listener(self, listener: Callable[[str, Any], None]):
        """Register a callback for queue events."""
        self._listeners.append(listener)
        
    def _emit(self, event_type: str, payload: Any):
        """Internal method to emit events to registered listeners."""
        for listener in self._listeners:
            try:
                listener(event_type, payload)
            except Exception:
                pass

    def add_job(self, params: Dict[str, Any]) -> str:
        """Add a new job to the queue."""
        job_id = str(uuid.uuid4())
        job = Job(id=job_id, params=params)
        self._jobs[job_id] = job
        self._emit("JOB_ADDED", {"job_id": job_id, "job": job})
        return job_id
        
    def remove_job(self, job_id: str):
        """Remove a job entirely from the queue."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._emit("JOB_REMOVED", {"job_id": job_id})
            
    def pause_job(self, job_id: str):
        """Pause a job."""
        job = self.get_job(job_id)
        if job and job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.status = JobStatus.PAUSED
            job.status_message = "Paused"
            self._emit("JOB_PAUSED", {"job_id": job_id})
            
    def resume_job(self, job_id: str):
        """Resume a paused job."""
        job = self.get_job(job_id)
        if job and job.status == JobStatus.PAUSED:
            job.status = JobStatus.PENDING
            job.status_message = "Resumed"
            self._emit("JOB_RESUMED", {"job_id": job_id})
            
    def cancel_job(self, job_id: str):
        """Cancel an ongoing or pending job."""
        job = self.get_job(job_id)
        if job and job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.status = JobStatus.CANCELLED
            job.status_message = "Cancelled"
            self._emit("JOB_CANCELLED", {"job_id": job_id})
            
    def cancel_all(self):
        """Cancel all ongoing or pending jobs."""
        for job_id, job in list(self._jobs.items()):
            if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.status = JobStatus.CANCELLED
                job.status_message = "Cancelled"
                self._emit("JOB_CANCELLED", {"job_id": job_id})
            
    def track_status(self, job_id: str, status: JobStatus, progress: int = None, message: str = None, error: str = None):
        """Update job progress and state."""
        job = self.get_job(job_id)
        if job:
            job.status = status
            if progress is not None:
                job.progress = progress
            if message is not None:
                job.status_message = message
            if error is not None:
                job.error_message = error
            self._emit("JOB_STATUS_CHANGED", {"job_id": job_id, "job": job})

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a specific job."""
        return self._jobs.get(job_id)
        
    def get_all_jobs(self) -> List[Job]:
        """Retrieve all current jobs."""
        return list(self._jobs.values())

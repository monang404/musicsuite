from typing import List, Optional, Callable
from ui.workers.base_worker import BaseWorker
from ui.viewmodels.process_vm import WorkflowJob
from ui.core.service_container import ServiceContainer

class WorkflowWorker(BaseWorker):
    """
    Background worker for processing a WorkflowJob via the WorkflowService.
    Ensures long-running audio processing does not block the UI.
    """
    def __init__(self, job_id: str, job_dto: WorkflowJob, parent=None):
        super().__init__(parent)
        self.job_id = job_id
        self.job_dto = job_dto
        
        # Use ServiceContainer
        container = ServiceContainer()
        self._workflow_service = container.workflow_service
        
    def _execute_work(self):
        """
        Executes the workflow. Emits progress via callbacks and
        returns the list of output files upon completion.
        """
        # We map the progress_callback to emit the BaseWorker progress signal.
        # BaseWorker progress signal expects (str, float)
        import time
        self._last_progress_time = 0.0
        
        def handle_progress(message: str):
            now = time.time()
            if now - self._last_progress_time > 0.05:
                self.progress.emit(message, 0.0)
                self._last_progress_time = now
            
        cancel_check_fn = lambda: self.is_cancelled()
        
        url = self.job_dto.source.url if self.job_dto.source else ""
        entity_type = getattr(self.job_dto.source, "entity_type", "compilation") if self.job_dto.source else "compilation"
        
        if entity_type == "playlist":
            # For playlists, source should be a PlaylistSource and we pass its entries
            entries = getattr(self.job_dto.source, "entries", [])
            output_files = self._workflow_service.process_playlist_workflow(
                entries=entries,
                output_dir=self.job_dto.output_folder,
                audio_format=self.job_dto.audio_format,
                bitrate=self.job_dto.bitrate,
                naming_pattern=self.job_dto.naming_pattern,
                progress_callback=handle_progress,
                cancel_check=cancel_check_fn
            )
        else:
            output_files = self._workflow_service.process_full_workflow(
                url=url,
                output_dir=self.job_dto.output_folder,
                audio_format=self.job_dto.audio_format,
                bitrate=self.job_dto.bitrate,
                naming_pattern=self.job_dto.naming_pattern,
                progress_callback=handle_progress,
                cancel_check=cancel_check_fn
            )
        
        if self.is_cancelled():
            self.cancelled.emit()
        else:
            self.completed.emit(output_files)

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QWidget
)
from PySide6.QtCore import Qt
from ui.screens.base_screen import BaseScreen
from ui.viewmodels.queue_vm import QueueViewModel
from services.queue_service import JobStatus

class JobWidget(QWidget):
    def __init__(self, job, viewmodel: QueueViewModel, parent=None):
        super().__init__(parent)
        self.job = job
        self.viewmodel = viewmodel
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = self.job.id
        if "workflow_dto" in self.job.params and self.job.params["workflow_dto"].source:
            title = self.job.params["workflow_dto"].source.title
            
        self.lbl_info = QLabel(f"{title} [{self.job.status.value}]")
        self.lbl_msg = QLabel(self.job.status_message or "")
        
        layout.addWidget(self.lbl_info, stretch=2)
        layout.addWidget(self.lbl_msg, stretch=3)
        
        # Actions
        if self.job.status in (JobStatus.RUNNING, JobStatus.PENDING):
            btn_pause = QPushButton("Pause")
            btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_pause.clicked.connect(lambda: self.viewmodel.pause_job(self.job.id))
            layout.addWidget(btn_pause)
            
            btn_cancel = QPushButton("Cancel")
            btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cancel.clicked.connect(lambda: self.viewmodel.cancel_job(self.job.id))
            layout.addWidget(btn_cancel)
            
        elif self.job.status == JobStatus.PAUSED:
            btn_resume = QPushButton("Resume")
            btn_resume.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_resume.clicked.connect(lambda: self.viewmodel.resume_job(self.job.id))
            layout.addWidget(btn_resume)
            
            btn_cancel = QPushButton("Cancel")
            btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cancel.clicked.connect(lambda: self.viewmodel.cancel_job(self.job.id))
            layout.addWidget(btn_cancel)
            
        elif self.job.status in (JobStatus.FAILED, JobStatus.CANCELLED):
            btn_retry = QPushButton("Retry")
            btn_retry.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_retry.clicked.connect(lambda: self.viewmodel.retry_job(self.job.id))
            layout.addWidget(btn_retry)
            

class QueueScreen(BaseScreen):
    """
    Queue Screen displays jobs according to their statuses.
    Follows BaseScreen architectural patterns and communicates exclusively through QueueViewModel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.bind_viewmodel(QueueViewModel())
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Queue")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout.addWidget(lbl_title)
        
        # Active Jobs
        self.layout.addWidget(QLabel("Active Jobs"))
        self.list_active = QListWidget()
        self.layout.addWidget(self.list_active)
        
        # Queued Jobs
        self.layout.addWidget(QLabel("Queued Jobs"))
        self.list_queued = QListWidget()
        self.layout.addWidget(self.list_queued)
        
        # Completed Jobs
        self.layout.addWidget(QLabel("Completed Jobs"))
        self.list_completed = QListWidget()
        self.layout.addWidget(self.list_completed)
        
        # Failed Jobs
        self.layout.addWidget(QLabel("Failed Jobs"))
        self.list_failed = QListWidget()
        self.layout.addWidget(self.list_failed)
        
    def bind_viewmodel(self, viewmodel: QueueViewModel):
        super().bind_viewmodel(viewmodel)
        self.viewmodel.queue_updated.connect(self.refresh_lists)
        self.refresh_lists()
        
    def on_navigated(self, **kwargs):
        if "job" in kwargs:
            self.viewmodel.add_workflow_job(kwargs["job"])
            
    def refresh_lists(self):
        if not self.viewmodel:
            return
            
        self._populate_list(self.list_active, self.viewmodel.active_jobs)
        self._populate_list(self.list_queued, self.viewmodel.queued_jobs)
        self._populate_list(self.list_completed, self.viewmodel.completed_jobs)
        self._populate_list(self.list_failed, self.viewmodel.failed_jobs)
        
    def _populate_list(self, list_widget: QListWidget, jobs):
        list_widget.clear()
        for job in jobs:
            item = QListWidgetItem(list_widget)
            widget = JobWidget(job, self.viewmodel)
            item.setSizeHint(widget.sizeHint())
            list_widget.setItemWidget(item, widget)

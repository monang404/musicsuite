import subprocess
import contextvars
import logging
from PySide6.QtCore import QThread, Signal
from typing import Any

# Declare context variable to track the active worker in the execution context (including thread pools)
active_worker_var = contextvars.ContextVar("active_worker", default=None)

# Store original Popen before hooking
_original_popen = subprocess.Popen

class custom_popen(_original_popen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Check if we are running in the context of an active worker
        worker = active_worker_var.get()
        if worker is not None:
            cmd = args[0] if args else kwargs.get("args", [])
            cmd_parts = []
            if isinstance(cmd, list):
                for part in cmd:
                    if isinstance(part, bytes):
                        cmd_parts.append(part.decode("utf-8", errors="ignore"))
                    else:
                        cmd_parts.append(str(part))
            elif isinstance(cmd, bytes):
                cmd_parts = [cmd.decode("utf-8", errors="ignore")]
            else:
                cmd_parts = [str(cmd)]
                
            cmd_lower = " ".join(cmd_parts).lower()
            if "ffmpeg" in cmd_lower or "yt-dlp" in cmd_lower:
                worker.track_process(self)

# Hook Popen
subprocess.Popen = custom_popen


class BaseWorker(QThread):
    """
    Base class for all asynchronous UI workers.
    Ensures long-running service calls do not block the main Qt event loop.
    Provides a standardized signal interface.
    """
    
    # Standard Signal Interface
    started = Signal()
    progress = Signal(str, float)  # message, percentage (0.0 to 1.0)
    completed = Signal(object)     # Result payload
    failed = Signal(str)           # Error message
    cancelled = Signal()           # Cancellation acknowledgement
    
    active_workers = []
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelled = False
        self._child_processes = []
        BaseWorker.active_workers.append(self)
        self.finished.connect(self._on_finished)
        
    def _on_finished(self):
        if self in BaseWorker.active_workers:
            BaseWorker.active_workers.remove(self)
            
    def track_process(self, proc):
        """Record process handle and PID inside worker lifecycle."""
        self._child_processes.append({
            "handle": proc,
            "pid": proc.pid
        })
        
    def terminate_child_processes(self):
        """Terminate only tracked child processes associated with this worker."""
        # 1. Ask all child processes to terminate
        for proc_info in list(self._child_processes):
            proc = proc_info["handle"]
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception as e:
                logging.error(f"Failed to terminate process {proc.pid}", exc_info=True)
                
        # 2. Wait up to 1 second in parallel for processes to shut down
        import time
        start_time = time.time()
        running = [p["handle"] for p in self._child_processes if p["handle"].poll() is None]
        while running and (time.time() - start_time) < 1.0:
            running = [p for p in running if p.poll() is None]
            time.sleep(0.05)
            
        # 3. Kill any remaining processes
        for proc in running:
            try:
                proc.kill()
                proc.wait()
            except Exception as e:
                logging.error(f"Failed to kill process {proc.pid}", exc_info=True)
        
    def cancel(self):
        """
        Requests the worker to cancel its current operation.
        The underlying run() implementation must check self.is_cancelled() periodically.
        """
        self._is_cancelled = True
        self.terminate_child_processes()
        
    def is_cancelled(self) -> bool:
        """
        Returns whether cancellation has been requested.
        """
        return self._is_cancelled
        
    def run(self):
        """
        The main execution block. Must be overridden by subclasses.
        Ensure to emit started, progress, completed, failed, and cancelled appropriately.
        """
        token = active_worker_var.set(self)
        self.started.emit()
        try:
            self._execute_work()
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            active_worker_var.reset(token)
            
    def _execute_work(self):
        """
        Override this method in subclasses to perform the actual background work.
        """
        raise NotImplementedError("Subclasses must implement _execute_work()")



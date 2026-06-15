from ui.workers.base_worker import BaseWorker
from ui.core.service_container import ServiceContainer

class SearchWorker(BaseWorker):
    """
    Worker for performing background searches without blocking the UI.
    """
    def __init__(self, query: str, parent=None):
        super().__init__(parent)
        self.query = query
        self.search_service = ServiceContainer().search_service

    def _execute_work(self):
        """
        Executes the search and emits detailed progress steps.
        """
        if self.is_cancelled():
            self.cancelled.emit()
            return
            
        self.progress.emit("Menganalisis kueri pencarian...", 0.1)
        
        query = self.query
        is_url = query.startswith("http://") or query.startswith("https://")
        
        import concurrent.futures
        from services.security import validate_url
        
        try:
            if is_url:
                self.progress.emit("Memvalidasi format URL...", 0.2)
                validate_url(query)
                self.progress.emit("Mengambil metadata dari sumber...", 0.5)
                final_results = self.search_service.resolve_query(query)
                self.progress.emit("Mengevaluasi hasil temuan...", 0.8)
            else:
                self.progress.emit("Menyiapkan pencarian playlist dan kompilasi...", 0.2)
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    self.progress.emit("Mencari data yang relevan secara paralel...", 0.3)
                    future_comp = executor.submit(self.search_service.search_compilation, query)
                    future_play = executor.submit(self.search_service.search_playlist, query)
                    
                    self.progress.emit("Menunggu hasil dari database/YouTube...", 0.5)
                    try:
                        compilations = future_comp.result()
                    except Exception:
                        compilations = []
                        
                    self.progress.emit("Mengekstrak metadata playlist...", 0.7)
                    try:
                        import time
                        start_time = time.time()
                        playlists = future_play.result()
                    except Exception as e:
                        playlists = None
                    self.progress.emit("Mengurutkan berdasarkan relevansi (confidence score)...", 0.9)
                    final_results = {
                        "compilations": compilations,
                        "playlists": playlists
                    }

            if self.is_cancelled():
                self.cancelled.emit()
                return
                
            self.progress.emit("Menyiapkan tampilan hasil pencarian...", 1.0)
            
            # Inject Debug Reporter
            from ui.debug_reporter import DebugSearchReporter
            reporter = DebugSearchReporter()
            reporter.reset()
            reporter.search_query = self.query
            
            total_returned = 0
            if "compilations" in final_results and final_results["compilations"]:
                total_returned += sum(len(g.sources) for g in final_results["compilations"])
            if "playlists" in final_results and final_results["playlists"]:
                total_returned += sum(len(g.sources) for g in final_results["playlists"])
            
            reporter.search_returned = total_returned
            reporter.signal_sent = total_returned
            
            self.completed.emit(final_results)
            
        except Exception as e:
            if not self.is_cancelled():
                raise e

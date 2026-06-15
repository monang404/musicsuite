class ServiceContainer:
    """
    Centralized Dependency Injection container for the UI layer.
    Ensures screens and viewmodels share the same service instances.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceContainer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        # Initialize services as None to allow lazy loading or explicit registration
        self._search_service = None
        self._timestamp_service = None
        self._workflow_service = None
        self._queue_service = None
        self._result_store = None
        self._dependency_service = None
        self._initialized = True
        
    @property
    def search_service(self):
        if self._search_service is None:
            from services.search_service import SearchService
            self._search_service = SearchService()
        return self._search_service
        
    @property
    def workflow_service(self):
        if self._workflow_service is None:
            # Assuming standard naming convention based on architecture plans
            from services.workflow_service import WorkflowService
            self._workflow_service = WorkflowService()
        return self._workflow_service
        
    @property
    def queue_service(self):
        if self._queue_service is None:
            from services.queue_service import QueueService
            self._queue_service = QueueService()
        return self._queue_service
        
    @property
    def timestamp_service(self):
        if self._timestamp_service is None:
            from services.timestamp_service import TimestampService
            self._timestamp_service = TimestampService()
        return self._timestamp_service
        
    @property
    def result_store(self):
        if self._result_store is None:
            from services.result_store import ResultStore
            self._result_store = ResultStore()
        return self._result_store
        
    @property
    def dependency_service(self):
        if self._dependency_service is None:
            from services.dependency_service import DependencyService
            self._dependency_service = DependencyService()
        return self._dependency_service
        
    def register_services(self, search=None, timestamp=None, workflow=None, queue=None, store=None):
        """
        Allows explicit injection of service instances (e.g., for testing or specific configurations).
        """
        if search:
            self._search_service = search
        if timestamp:
            self._timestamp_service = timestamp
        if workflow:
            self._workflow_service = workflow
        if queue:
            self._queue_service = queue
        if store:
            self._result_store = store


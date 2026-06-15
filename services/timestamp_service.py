from typing import Callable, Optional, Tuple, Dict, Any
from engines.timestamp.service import TimestampService as EngineTimestampService

class TimestampService:
    """Service layer wrapper for the Timestamp Engine."""

    def __init__(self):
        self._engine = EngineTimestampService()

    def generate_timestamps(
        self, 
        youtube_url: str, 
        info: Dict[str, Any], 
        audio_path: Optional[str] = None, 
        progress_callback: Optional[Callable[[str], None]] = None, 
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> Tuple[str, str]:
        """
        Generate timestamps for a given video.
        
        Args:
            youtube_url: The URL of the YouTube video.
            info: Video metadata dictionary.
            audio_path: Optional path to the downloaded audio file.
            progress_callback: Optional callback for progress updates.
            cancel_check: Optional callback to check for cancellation.
            
        Returns:
            Tuple containing the generated timestamp text and the method used.
        """
        return self._engine.generate_timestamps(
            youtube_url=youtube_url, 
            info=info, 
            audio_path=audio_path, 
            progress_callback=progress_callback, 
            cancel_check=cancel_check
        )

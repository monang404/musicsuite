from pathlib import Path
from typing import Callable, Optional, Dict, Any
from engines.downloader.service import DownloaderService as EngineDownloaderService
from services.security import validate_url

class DownloaderService:
    """Service layer wrapper for the Downloader Engine."""

    def __init__(self):
        self._engine = EngineDownloaderService()

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Fetch video metadata without downloading.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary containing video metadata.
        """
        validate_url(url)
        return self._engine.get_video_info(url)
        
    def download_audio(
        self,
        url: str,
        output_dir: str | Path,
        export_format: str = "mp3",
        export_bitrate: str = "320k",
        progress_callback: Optional[Callable[[int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        Download audio from a YouTube video as the specified export format.
        
        Args:
            url: YouTube video URL
            output_dir: Directory to save the downloaded file
            export_format: Output format (mp3, wav, flac, aac)
            export_bitrate: Quality bitrate for lossy formats (e.g., 320k)
            progress_callback: Optional callback(percent, status_text)
            cancel_check: Optional callback returning True if download should abort
            
        Returns:
            Full path to the downloaded audio file
        """
        validate_url(url)
        return self._engine.download_audio(
            url=url,
            output_dir=output_dir,
            export_format=export_format,
            export_bitrate=export_bitrate,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )

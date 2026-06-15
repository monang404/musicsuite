from pathlib import Path
from typing import Callable, Optional, List
from engines.splitter.service import SplitterService as EngineSplitterService
from engines.timestamp.models.track import Track

class SplitterService:
    """Service layer wrapper for the Splitter Engine."""

    def __init__(self):
        self._engine = EngineSplitterService()

    def check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is available in PATH.
        
        Returns:
            True if FFmpeg is available, False otherwise.
        """
        return self._engine.check_ffmpeg()

    def split_audio(
        self,
        source_file: str | Path,
        songs: List[Track],
        output_dir: str | Path,
        output_format: str = "mp3",
        bitrate: str = "320k",
        naming_pattern: str = "{index:03d} - {title}",
        progress_callback: Optional[Callable[[int, str, int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> List[str]:
        """
        Split an audio file into individual song files using FFmpeg.
        
        Args:
            source_file: Path to the source audio file
            songs: List of Track objects with start/end times
            output_dir: Directory to write output files
            output_format: Destination audio format (mp3, wav, flac, aac)
            bitrate: Quality bitrate for lossy formats (e.g. 320k)
            naming_pattern: Filename template (e.g. "{index:03d} - {title}")
            progress_callback: Optional callback(percent, status_text, current_idx, total_idx)
            cancel_check: Optional callback returning True if splitting should abort
            
        Returns:
            List of paths to the created output files
        """
        return self._engine.split_audio(
            source_file=source_file,
            songs=songs,
            output_dir=output_dir,
            output_format=output_format,
            bitrate=bitrate,
            naming_pattern=naming_pattern,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )

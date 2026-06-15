import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List, Tuple

from services.downloader_service import DownloaderService
from services.timestamp_service import TimestampService
from services.splitter_service import SplitterService
from engines.timestamp.parsers.timestamp_parser import TimestampParser
from engines.timestamp.models.track import Track

class WorkflowService:
    """Service for orchestrating the complete music processing workflow."""

    def __init__(self):
        self.downloader = DownloaderService()
        self.timestamp = TimestampService()
        self.splitter = SplitterService()

    def process_full_workflow(
        self,
        url: str,
        output_dir: str | Path,
        audio_format: str = "mp3",
        bitrate: str = "320k",
        naming_pattern: str = "{index:03d} - {title}",
        progress_callback: Optional[Callable[[str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> List[str]:
        """
        Orchestrates the entire process: download -> timestamp -> split.
        
        Args:
            url: YouTube video URL
            output_dir: Directory to save downloaded and split files
            audio_format: Output format for the final split files
            bitrate: Quality bitrate for lossy formats
            naming_pattern: Filename template for split files
            progress_callback: Callback for string progress updates
            cancel_check: Callback to check for cancellation
            
        Returns:
            List of paths to the created split files
        """
        if progress_callback:
            progress_callback("Fetching video info...")
        
        output_dir = str(Path(output_dir).resolve())
        
        if cancel_check and cancel_check():
            return []
            
        info = self.downloader.get_video_info(url)
        
        if progress_callback:
            progress_callback("Downloading audio...")
            
        def dl_progress(percent: int, status: str):
            if progress_callback:
                progress_callback(f"Downloading: {percent}% - {status}")
                
        audio_path = self.downloader.download_audio(
            url=url,
            output_dir=output_dir,
            export_format=audio_format,
            export_bitrate=bitrate,
            progress_callback=dl_progress,
            cancel_check=cancel_check
        )
        
        if progress_callback:
            progress_callback("Generating timestamps...")
            
        timestamp_text, _method_used = self.timestamp.generate_timestamps(
            youtube_url=url,
            info=info,
            audio_path=audio_path,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )
        
        if progress_callback:
            progress_callback("Parsing timestamps...")
            
        duration = info.get("duration", 0)
        tracks = TimestampParser.parse_formatted(timestamp_text, audio_duration=duration)
        
        if progress_callback:
            progress_callback("Splitting audio...")
            
        def split_progress(percent: int, status: str, current: int, total: int):
            if progress_callback:
                progress_callback(f"Splitting ({current}/{total}): {percent}% - {status}")
                
        output_files = self.splitter.split_audio(
            source_file=audio_path,
            songs=tracks,
            output_dir=output_dir,
            output_format=audio_format,
            bitrate=bitrate,
            naming_pattern=naming_pattern,
            progress_callback=split_progress,
            cancel_check=cancel_check
        )
        
        if progress_callback:
            progress_callback("Membersihkan file cache sementara...")
            
        try:
            Path(audio_path).unlink()
        except Exception as e:
            logging.warning(f"Gagal menghapus file sumber {audio_path}: {e}")
        
        if progress_callback:
            progress_callback("Workflow complete.")
            
        return output_files

    def process_playlist_workflow(
        self,
        entries: List[Any], # List[PlaylistEntry]
        output_dir: str | Path,
        audio_format: str = "mp3",
        bitrate: str = "320k",
        naming_pattern: str = "{index:03d} - {title}",
        progress_callback: Optional[Callable[[str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> List[str]:
        """
        Orchestrates the process for a playlist: download each entry directly.
        """
        output_files = []
        total = len(entries)
        output_dir = str(Path(output_dir).resolve())
        
        for i, entry in enumerate(entries, 1):
            if cancel_check and cancel_check():
                break
                
            if progress_callback:
                progress_callback(f"Downloading track {i}/{total}: {entry.title}")
                
            def dl_progress(percent: int, status: str):
                if progress_callback:
                    progress_callback(f"Track {i}/{total} ({percent}%): {status}")
            
            try:
                # We need a proper filename for the entry
                # Currently we rely on DownloaderService generating it or renaming it later
                # We can just let downloader download it
                audio_path = self.downloader.download_audio(
                    url=entry.url,
                    output_dir=output_dir,
                    export_format=audio_format,
                    export_bitrate=bitrate,
                    progress_callback=dl_progress,
                    cancel_check=cancel_check
                )
                if audio_path:
                    output_files.append(audio_path)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Failed to download {entry.title}: {e}")
                    
        if progress_callback:
            progress_callback("Playlist workflow complete.")
            
        return output_files

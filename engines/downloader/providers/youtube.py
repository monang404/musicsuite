"""
YouTube audio downloader for Smart Music Splitter.
Uses yt-dlp to download audio from YouTube videos as MP3.
"""

import os
from pathlib import Path
from typing import Callable, Optional

import yt_dlp
from engines.downloader.models.exceptions import DownloadError
from services.security import validate_url


def get_video_info(url: str) -> dict:
    """
    Fetch video metadata without downloading.
    
    Args:
        url: YouTube video URL
    
    Returns:
        Dictionary with 'title', 'duration', 'thumbnail' keys
    """
    validate_url(url)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "id": info.get("id", ""),
                "description": info.get("description", ""),   # for timestamp parsing
                "chapters": info.get("chapters", []),          # for chapter-based split
            }
    except Exception as e:
        raise DownloadError(f"Gagal mengambil info video: {str(e)}")


def download_audio(
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
    
    Raises:
        DownloadError: If the download fails or is cancelled
    """
    validate_url(url)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_dir / "%(title)s.%(ext)s")
    downloaded_file = [None]
    
    def progress_hook(d):
        if cancel_check and cancel_check():
            raise Exception("Download cancelled by user")
            
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed", 0) or 0
            
            # Format speed
            if speed >= 1024 * 1024:
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
            elif speed > 0:
                speed_str = f"{speed / 1024:.0f} KB/s"
            else:
                speed_str = "..."
            
            # Format ETA
            eta = d.get("eta")
            eta_str = ""
            if eta is not None:
                m = int(eta) // 60
                s = int(eta) % 60
                eta_str = f"~{m}m {s}s" if m > 0 else f"~{s}s"
            
            # Format size
            if total > 0 and progress_callback:
                percent = int((downloaded / total) * 100)  # 0-100% for download
                dl_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                status = f"Mengunduh... {dl_mb:.1f}/{total_mb:.1f} MB  ⚡ {speed_str}"
                if eta_str:
                    status += f"  ⌛ {eta_str}"
                progress_callback(percent, status)
            elif progress_callback:
                dl_mb = downloaded / (1024 * 1024)
                status = f"Mengunduh... {dl_mb:.1f} MB  ⚡ {speed_str}"
                if eta_str:
                    status += f"  ⌛ {eta_str}"
                progress_callback(10, status)
        
        elif d["status"] == "finished":
            if progress_callback:
                progress_callback(100, "Mengunduh selesai!")
                progress_callback(0, f"Mengkonversi ke {export_format.upper()}...")
            downloaded_file[0] = d.get("filename", "")

    def postprocessor_hook(d):
        if cancel_check and cancel_check():
            raise Exception("Download cancelled by user")

    # Map format and quality configurations
    # supported export_format: "mp3", "wav", "flac", "aac"
    fmt = export_format.lower()
    postprocessor = {
        "key": "FFmpegExtractAudio",
        "preferredcodec": fmt,
    }
    if fmt in ("mp3", "aac"):
        # Quality can be specified in kbps for mp3/aac postprocessor
        postprocessor["preferredquality"] = export_bitrate.rstrip("k")
    else:
        postprocessor["preferredquality"] = "0"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [postprocessor],
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Determine the final filename
            title = info.get("title", "audio")
            expected_path = output_dir / f"{title}.{export_format}"
            
            # Search for the actual file
            if expected_path.exists():
                final_path = str(expected_path)
            else:
                files = list(output_dir.glob(f"*.{export_format}"))
                if not files and export_format == "aac":
                    files = list(output_dir.glob("*.m4a"))
                if files:
                    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    final_path = str(files[0])
                else:
                    raise DownloadError(f"File {export_format} tidak ditemukan setelah download.")
            
            if progress_callback:
                progress_callback(100, "Konversi selesai!")
            
            return final_path
    
    except yt_dlp.utils.DownloadError as e:
        if cancel_check and cancel_check():
            raise DownloadError("Download cancelled by user")
        raise DownloadError(f"Gagal mengunduh video: {str(e)}")
    except Exception as e:
        if cancel_check and cancel_check():
            raise DownloadError("Download cancelled by user")
        if isinstance(e, DownloadError):
            raise
        raise DownloadError(f"Gagal mengunduh video: {str(e)}")

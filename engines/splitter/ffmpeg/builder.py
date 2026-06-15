"""
FFmpeg command building utilities for audio splitting.
"""

import re


def sanitize_filename(name: str) -> str:
    """
    Remove or replace characters that are illegal in Windows filenames.

    Args:
        name: Raw filename string

    Returns:
        Sanitized filename safe for Windows
    """
    # Replace illegal characters with underscore
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, "_", name)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(" .")
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


def format_ffmpeg_time(seconds: int) -> str:
    """
    Format seconds into HH:MM:SS format for FFmpeg.

    Args:
        seconds: Total seconds

    Returns:
        Formatted time string like "01:23:45"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def build_copy_command(source_file: str, output_path: str,
                       start_seconds: int, end_seconds: int) -> list[str]:
    """Build FFmpeg stream-copy command for a song segment."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", source_file,
        "-ss", format_ffmpeg_time(start_seconds),
    ]
    if end_seconds > 0:
        cmd.extend(["-to", format_ffmpeg_time(end_seconds)])
    cmd.extend([
        "-c", "copy",
        "-map", "a",
        output_path,
    ])
    return cmd


def build_reencode_command(source_file: str, output_path: str,
                           start_seconds: int, end_seconds: int,
                           output_format: str = "mp3",
                           bitrate: str = "320k") -> list[str]:
    """Build FFmpeg re-encode fallback command for a song segment."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", source_file,
        "-ss", format_ffmpeg_time(start_seconds),
    ]
    if end_seconds > 0:
        cmd.extend(["-to", format_ffmpeg_time(end_seconds)])
        
    fmt = output_format.lower()
    if fmt == "mp3":
        cmd.extend([
            "-acodec", "libmp3lame",
            "-ab", bitrate,
        ])
    elif fmt == "wav":
        cmd.extend([
            "-acodec", "pcm_s16le",
        ])
    elif fmt == "flac":
        cmd.extend([
            "-acodec", "flac",
        ])
    elif fmt == "aac":
        cmd.extend([
            "-acodec", "aac",
            "-ab", bitrate,
        ])
    else:
        cmd.extend([
            "-ab", bitrate,
        ])
        
    cmd.append(output_path)
    return cmd

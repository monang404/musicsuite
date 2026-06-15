"""
FFmpeg subprocess execution for exporting split audio segments.
"""

import os
import subprocess
from pathlib import Path

from engines.splitter.ffmpeg.builder import build_copy_command, build_reencode_command
from engines.splitter.models.exceptions import SplitError


def run_ffmpeg_export(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """Run an FFmpeg command and return the completed process."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def export_song_segment(
    source_file: str,
    output_path: str,
    start_seconds: int,
    end_seconds: int,
    title: str,
    output_format: str = "mp3",
    bitrate: str = "320k",
) -> None:
    """
    Export a single song segment using FFmpeg.

    Tries stream copy first if formats match, otherwise re-encodes.

    Raises:
        SplitError: If FFmpeg attempts fail or timeout.
    """
    source_ext = Path(source_file).suffix.lower().lstrip(".")
    can_copy = (source_ext == output_format.lower())

    if can_copy:
        cmd = build_copy_command(source_file, output_path, start_seconds, end_seconds)
        try:
            result = run_ffmpeg_export(cmd, timeout=120)
            if result.returncode == 0:
                return
        except Exception:
            pass

    # Re-encode fallback or direct encoder run
    cmd_reencode = build_reencode_command(
        source_file, output_path, start_seconds, end_seconds,
        output_format=output_format,
        bitrate=bitrate,
    )
    
    try:
        result2 = run_ffmpeg_export(cmd_reencode, timeout=300)
        if result2.returncode != 0:
            raise SplitError(
                f"Gagal memproses lagu '{title}': {result2.stderr[:200]}"
            )

    except subprocess.TimeoutExpired:
        raise SplitError(f"Timeout saat memproses lagu '{title}'.")
    except SplitError:
        raise
    except Exception as e:
        raise SplitError(f"Gagal memproses lagu '{title}': {str(e)}")

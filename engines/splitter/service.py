import os
import shutil
import logging
from pathlib import Path
from typing import Callable, Optional

from engines.timestamp.models.track import Track
from engines.splitter.exporters.ffmpeg_exporter import export_song_segment
from engines.splitter.ffmpeg.builder import sanitize_filename
from engines.splitter.models.exceptions import SplitError


class SplitterService:
    """Facade service for audio splitting operations."""

    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available in PATH."""
        return shutil.which("ffmpeg") is not None

    def _emit_split_progress(
        self,
        progress_callback: Optional[Callable[[int, str, int, int], None]],
        index: int,
        total: int,
        title: str,
    ) -> None:
        """Emit progress for the current song being split."""
        if progress_callback:
            percent = int((index / total) * 100)
            progress_callback(percent, title, index + 1, total)

    def _emit_split_complete(
        self,
        progress_callback: Optional[Callable[[int, str, int, int], None]],
        total: int,
    ) -> None:
        """Emit completion progress after all songs are split."""
        if progress_callback:
            progress_callback(100, f"Selesai! {total} lagu berhasil dibuat.", total, total)

    def split_audio(
        self,
        source_file: str | Path,
        songs: list[Track],
        output_dir: str | Path,
        output_format: str = "mp3",
        bitrate: str = "320k",
        naming_pattern: str = "{index:03d} - {title}",
        progress_callback: Optional[Callable[[int, str, int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> list[str]:
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

        Raises:
            SplitError: If FFmpeg fails, source file is missing, or cancelled
        """
        source_file = Path(source_file)
        output_dir = Path(output_dir)

        if not source_file.exists():
            raise SplitError(f"File sumber tidak ditemukan: {source_file}")

        if not self.check_ffmpeg():
            raise SplitError(
                "FFmpeg tidak ditemukan. Pastikan FFmpeg terinstall dan ada di PATH sistem."
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        output_files = []
        total = len(songs)

        for i, song in enumerate(songs):
            if cancel_check and cancel_check():
                for f in output_files:
                    try:
                        os.remove(f)
                    except Exception:
                        logging.warning(f"Failed to remove output file: {f}", exc_info=True)
                raise SplitError("Split cancelled by user")

            # Build output filename using the naming pattern
            safe_title = sanitize_filename(song.title)
            if not safe_title:
                safe_title = f"Track {song.index}"

            filename_without_ext = ""
            if naming_pattern and naming_pattern.strip():
                try:
                    filename_without_ext = naming_pattern.format(index=song.index, title=safe_title).strip()
                except Exception:
                    logging.warning(f"Failed to apply naming pattern: {naming_pattern}", exc_info=True)

            if not filename_without_ext:
                filename_without_ext = f"{song.index:03d} - {safe_title}"

            filename = f"{filename_without_ext}.{output_format}"
            output_path = output_dir / filename

            self._emit_split_progress(progress_callback, i, total, song.title)

            try:
                export_song_segment(
                    source_file=str(source_file),
                    output_path=str(output_path),
                    start_seconds=song.start_seconds,
                    end_seconds=song.end_seconds,
                    title=song.title,
                    output_format=output_format,
                    bitrate=bitrate,
                )
            except Exception as e:
                # If aborted during export or export failed, delete output file if it exists
                try:
                    if output_path.exists():
                        os.remove(output_path)
                except Exception:
                    logging.warning(f"Failed to remove output file during abort: {output_path}", exc_info=True)
                # Clean up all previously successfully written files as well on failure
                for f in output_files:
                    try:
                        os.remove(f)
                    except Exception:
                        logging.warning(f"Failed to clean up previously written file: {f}", exc_info=True)
                raise SplitError(str(e))

            output_files.append(str(output_path))

        # Check cancellation one last time before complete
        if cancel_check and cancel_check():
            for f in output_files:
                try:
                    os.remove(f)
                except Exception:
                    logging.warning(f"Failed to remove output file during cancellation: {f}", exc_info=True)
            raise SplitError("Split cancelled by user")

        self._emit_split_complete(progress_callback, total)

        return output_files

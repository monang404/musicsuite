import os
from typing import Callable, Optional, Tuple

from engines.timestamp.utils import AutoTimestampError, entries_to_text
from engines.timestamp.extractors.chapters import extract_chapters
from engines.timestamp.extractors.description import extract_description_timestamps
from engines.timestamp.extractors.comments import extract_comment_timestamps, extract_titles_from_comments
from engines.timestamp.extractors.silence import extract_silence_timestamps
from engines.timestamp.extractors.ocr import extract_thumbnail_ocr_timestamps
from engines.timestamp.parsers.title_parser import extract_titles_from_text


class TimestampService:
    @staticmethod
    def generate_timestamps(youtube_url: str, info: dict, audio_path: Optional[str] = None, progress_callback: Optional[Callable[[str], None]] = None, cancel_check: Optional[Callable[[], bool]] = None) -> Tuple[str, str]:
        def _progress(msg: str):
            if progress_callback:
                progress_callback(msg)

        if cancel_check and cancel_check(): raise AutoTimestampError("Auto-timestamp cancelled")
        _progress("Mencari chapters...")
        entries = extract_chapters(info)
        if entries: return entries_to_text(entries), "chapters"

        if cancel_check and cancel_check(): raise AutoTimestampError("Auto-timestamp cancelled")
        _progress("Mencari description...")
        entries = extract_description_timestamps(info)
        if entries: return entries_to_text(entries), "description"

        if cancel_check and cancel_check(): raise AutoTimestampError("Auto-timestamp cancelled")
        _progress("Mencari comments...")
        entries = extract_comment_timestamps(youtube_url)
        if entries: return entries_to_text(entries), "comments"

        if audio_path and os.path.exists(audio_path):
            desc_titles = extract_titles_from_text(info.get("description", ""), video_title=info.get("title", ""))
            if len(desc_titles) < 2: desc_titles = []

            comm_titles = []
            if not desc_titles:
                comm_titles = extract_titles_from_comments(youtube_url, video_title=info.get("title", ""))
                if len(comm_titles) < 2: comm_titles = []

            candidate_titles = desc_titles or comm_titles
            
            ocr_titles = []
            thumbnail_url = info.get("thumbnail", "")
            if thumbnail_url:
                ocr_text = extract_thumbnail_ocr_timestamps(thumbnail_url)
                if ocr_text:
                    ocr_titles = extract_titles_from_text(ocr_text, video_title=info.get("title", ""))
                    if len(ocr_titles) < 2: ocr_titles = []

            final_titles = ocr_titles if ocr_titles else candidate_titles
            method_used = "silence_ocr" if ocr_titles else "silence"

            entries = extract_silence_timestamps(audio_path, titles=final_titles, cancel_check=cancel_check)
            if entries: return entries_to_text(entries), method_used

        raise AutoTimestampError("Timestamp tidak dapat dideteksi otomatis.")

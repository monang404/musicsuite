from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from engines.search.models.track import Track

@dataclass
class ChapterParseResult:
    tracks: List[Track]
    chapter_count: int
    covers_full_duration: bool
    is_valid: bool

class ChapterParser:
    def parse(self, raw_chapters: Optional[List[Dict[str, Any]]], total_duration: int) -> ChapterParseResult:
        if not raw_chapters:
            return ChapterParseResult(tracks=[], chapter_count=0, covers_full_duration=False, is_valid=False)

        tracks = []
        for ch in raw_chapters:
            title = ch.get('title', '').strip()
            # Ignore empty titles or generic "Intro" if we want to be strict,
            # but usually we keep them as tracks unless specifically instructed to drop.
            start_time = float(ch.get('start_time', 0))
            end_time = ch.get('end_time')
            if end_time is not None:
                end_time = float(end_time)
            
            tracks.append(Track(
                title=title,
                start_time=start_time,
                end_time=end_time,
                source="chapter"
            ))

        chapter_count = len(tracks)
        is_valid = chapter_count >= 3
        
        covers_full_duration = False
        if chapter_count > 0 and total_duration > 0:
            last_track_end = tracks[-1].end_time or tracks[-1].start_time
            if abs(total_duration - last_track_end) <= 60.0:
                covers_full_duration = True

        return ChapterParseResult(
            tracks=tracks,
            chapter_count=chapter_count,
            covers_full_duration=covers_full_duration,
            is_valid=is_valid
        )

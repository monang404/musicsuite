from dataclasses import dataclass, field
from typing import List, Dict, Any
import hashlib

from engines.search.models.search_entity import SearchEntity
from engines.search.models.track import Track

@dataclass
class CompilationVideo(SearchEntity):
    duration: int = 0
    view_count: int = 0

    has_chapters: bool = False
    has_timestamps: bool = False
    chapters_cover_full_duration: bool = False
    timestamps_are_monotonic: bool = False

    chapter_count: int = 0
    timestamp_count: int = 0
    track_count: int = 0

    tracks: List[Track] = field(default_factory=list)
    is_deep_fetched: bool = False
    soft_penalty: int = 0
    entity_type: str = "compilation"

    @classmethod
    def from_ytdlp_info(cls, raw: Dict[str, Any]) -> "CompilationVideo":
        url = raw.get('url', raw.get('webpage_url', ''))
        
        # Generate short id from url
        source_id = ""
        if url:
            source_id = hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]

        return cls(
            id=source_id,
            url=url,
            title=raw.get('title', ''),
            channel=raw.get('uploader', raw.get('channel', '')),
            duration=int(raw.get('duration', 0) or 0),
            view_count=int(raw.get('view_count', 0) or 0),
            upload_date=raw.get('upload_date', ''),
            thumbnail_url=raw.get('thumbnail', '')
        )

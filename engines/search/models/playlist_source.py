from dataclasses import dataclass, field
from typing import List, Dict, Any
import hashlib

from engines.search.models.search_entity import SearchEntity

@dataclass
class PlaylistEntry:
    title: str
    url: str
    duration: int = 0
    thumbnail_url: str = ""
    channel: str = ""

@dataclass
class PlaylistSource(SearchEntity):
    playlist_id: str = ""
    item_count: int = 0
    entries: List[PlaylistEntry] = field(default_factory=list)
    is_official: bool = False
    soft_penalty: int = 0
    is_deep_fetched: bool = False
    entity_type: str = "playlist"
    # New relevance score fields (populated by PlaylistScorer)
    music_score: float = 0.0
    artist_confidence: float = 0.0
    metadata_quality: float = 0.0
    reject_reason: str = ""

    @classmethod
    def from_ytdlp_playlist_info(cls, raw: Dict[str, Any]) -> "PlaylistSource":
        url = raw.get('url', raw.get('webpage_url', ''))
        
        # Generate short id from url
        source_id = ""
        if url:
            source_id = hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]

        playlist_id = raw.get('id', '')
        raw_entries = raw.get('entries', []) or []
        entries = [
            PlaylistEntry(
                title=e.get('title', ''), 
                url=e.get('url', e.get('webpage_url', '')), 
                duration=int(e.get('duration', 0) or 0),
                thumbnail_url=e.get('thumbnails', [{'url': e.get('thumbnail', '')}])[-1].get('url', e.get('thumbnail', '')),
                channel=e.get('uploader', e.get('channel', ''))
            ) 
            for e in raw_entries
        ]

        uploader = raw.get('uploader', raw.get('channel', ''))
        title = raw.get('title', '')
        
        uploader_lower = uploader.lower() if uploader else ""
        title_lower = title.lower() if title else ""
        
        is_official = 'official' in uploader_lower or '- topic' in uploader_lower or 'official' in title_lower

        # For single JSON fetch of a playlist, thumbnails is usually a list
        thumbnail_url = ""
        thumbnails = raw.get('thumbnails', [])
        if thumbnails:
            thumbnail_url = thumbnails[-1].get('url', '')
        if not thumbnail_url:
            thumbnail_url = raw.get('thumbnail', '')

        return cls(
            id=source_id,
            url=url,
            title=title,
            channel=uploader,
            thumbnail_url=thumbnail_url,
            upload_date=raw.get('upload_date', ''),
            playlist_id=playlist_id,
            item_count=len(raw_entries),
            entries=entries,
            is_official=bool(is_official)
        )

from dataclasses import dataclass
from typing import List, Optional
from engines.search.models.track import Track
from engines.search.metadata.chapter_parser import ChapterParseResult
from engines.search.metadata.timestamp_parser import TimestampParseResult

@dataclass
class BuildResult:
    tracks: List[Track]
    track_count: int
    primary_source: str          # "chapter" | "timestamp" | "none"
    has_chapters: bool
    has_timestamps: bool
    chapters_cover_full_duration: bool
    timestamps_are_monotonic: bool

class TracklistBuilder:
    def build(
        self,
        chapter_result: Optional[ChapterParseResult] = None,
        timestamp_result: Optional[TimestampParseResult] = None,
    ) -> BuildResult:
        
        has_chapters = bool(chapter_result and chapter_result.is_valid)
        has_timestamps = bool(timestamp_result and timestamp_result.is_valid)
        
        chapters_cover = bool(chapter_result and chapter_result.covers_full_duration)
        timestamps_mono = bool(timestamp_result and timestamp_result.is_monotonic)

        # Prioritize chapters over timestamps
        if has_chapters and chapter_result is not None:
            return BuildResult(
                tracks=chapter_result.tracks,
                track_count=chapter_result.chapter_count,
                primary_source="chapter",
                has_chapters=has_chapters,
                has_timestamps=has_timestamps,
                chapters_cover_full_duration=chapters_cover,
                timestamps_are_monotonic=timestamps_mono
            )
        
        if has_timestamps and timestamp_result is not None:
            return BuildResult(
                tracks=timestamp_result.tracks,
                track_count=timestamp_result.timestamp_count,
                primary_source="timestamp",
                has_chapters=has_chapters,
                has_timestamps=has_timestamps,
                chapters_cover_full_duration=chapters_cover,
                timestamps_are_monotonic=timestamps_mono
            )

        return BuildResult(
            tracks=[],
            track_count=0,
            primary_source="none",
            has_chapters=has_chapters,
            has_timestamps=has_timestamps,
            chapters_cover_full_duration=chapters_cover,
            timestamps_are_monotonic=timestamps_mono
        )

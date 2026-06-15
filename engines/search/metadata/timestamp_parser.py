import re
from dataclasses import dataclass
from typing import List, Tuple, Optional
from engines.search.models.track import Track

@dataclass
class TimestampParseResult:
    tracks: List[Track]
    timestamp_count: int
    is_monotonic: bool
    is_valid: bool

TIMESTAMP_PATTERNS = [
    # Bracketed: "[03:22] Song Title" or "[03.22] Song Title"
    r'^\[(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\]\s+(.+)',
    # Numbered: "1. 03:22 - Song Title" or "1) 03.22 Song"
    r'^\d+[.)]\s*(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\s*[-–—]?\s*(.+)',
    # Bullet/Dash prefix: "- 03:22 Song Title" or "• 03.22 Song Title"
    r'^[-•*]\s*(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\s+(.+)',
    # Standard: "03:22 Song Title" or "1.03.22 Song Title"
    r'^(\d{1,2}[:.]\d{2}(?:[:.]\d{2})?)\s+(.+)',
]

class TimestampParser:
    def parse(self, description: Optional[str]) -> TimestampParseResult:
        if not description:
            return TimestampParseResult(tracks=[], timestamp_count=0, is_monotonic=False, is_valid=False)

        tracks = []
        lines = description.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in TIMESTAMP_PATTERNS:
                match = re.match(pattern, line)
                if match:
                    time_str = match.group(1).strip()
                    title = match.group(2).strip()
                    
                    # Clean up trailing dashes or unwanted characters from title
                    title = re.sub(r'^[-–—]\s*', '', title)
                    
                    try:
                        seconds = self._to_seconds(time_str)
                        tracks.append(Track(
                            title=title,
                            start_time=seconds,
                            source="timestamp"
                        ))
                        break # Stop checking other patterns if one matched
                    except ValueError:
                        pass
        
        # Calculate end times
        for i in range(len(tracks) - 1):
            tracks[i].end_time = tracks[i+1].start_time

        timestamp_count = len(tracks)
        is_monotonic, _ = self._validate_monotonic([t.start_time for t in tracks])
        is_valid = timestamp_count >= 3

        return TimestampParseResult(
            tracks=tracks,
            timestamp_count=timestamp_count,
            is_monotonic=is_monotonic,
            is_valid=is_valid
        )

    def _to_seconds(self, ts: str) -> float:
        ts = ts.replace('.', ':')
        parts = ts.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        raise ValueError(f"Invalid timestamp format: {ts}")

    def _validate_monotonic(self, times: List[float]) -> Tuple[bool, int]:
        violations = 0
        for i in range(1, len(times)):
            if times[i] <= times[i-1]:
                violations += 1
        return violations == 0, violations

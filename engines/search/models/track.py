from dataclasses import dataclass
from typing import Optional

@dataclass
class Track:
    title: str
    start_time: float
    end_time: Optional[float] = None
    source: str = "unknown"  # "chapter" | "timestamp" | "tracklist_only"

    def duration_seconds(self) -> Optional[float]:
        if self.end_time is not None:
            return max(0.0, self.end_time - self.start_time)
        return None

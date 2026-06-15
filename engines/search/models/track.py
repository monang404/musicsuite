from dataclasses import dataclass
from typing import Optional

@dataclass
class Track:
    title: str
    start_time: float
    end_time: Optional[float] = None
    source: str = "unknown"  # "chapter" | "timestamp" | "tracklist_only"

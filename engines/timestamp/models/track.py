from dataclasses import dataclass

@dataclass
class Track:
    index: int
    start_seconds: int
    end_seconds: int
    title: str
    raw_line: str
    line_number: int

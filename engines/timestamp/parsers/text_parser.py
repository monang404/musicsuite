from engines.timestamp.models.track import Track
"""
Timestamp parser for Smart Music Splitter.
Parses timestamp text in the format MM:SS|Title or HH:MM:SS|Title
into structured Track objects.
"""

import re
from dataclasses import dataclass


    # Line number in the input text


def time_to_seconds(time_str: str) -> int:
    """
    Convert a time string (MM:SS or HH:MM:SS) to total seconds.
    
    Args:
        time_str: Time string like "04:05" or "01:12:30"
    
    Returns:
        Total seconds as integer
    """
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"Invalid time format: {time_str}")


def seconds_to_time(seconds: int) -> str:
    """
    Convert total seconds to a formatted time string.
    
    Args:
        seconds: Total seconds
    
    Returns:
        Formatted string like "04:05" or "1:12:30"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_timestamps(text: str, audio_duration: int = 0) -> list[Track]:
    """
    Parse timestamp text into a list of Track objects.
    
    Args:
        text: Multi-line timestamp text
        audio_duration: Total audio duration in seconds (for last song's end time)
    
    Returns:
        List of Track objects with calculated start and end times
    """
    songs = []
    lines = text.strip().split("\n")
    
    # First pass: extract all valid entries
    entries = []
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue
        
        # Must contain separator
        if "|" not in line:
            continue
        
        parts = line.split("|", 1)
        time_str = parts[0].strip()
        title = parts[1].strip()
        
        try:
            start_sec = time_to_seconds(time_str)
        except (ValueError, IndexError):
            continue
        
        entries.append({
            "start": start_sec,
            "title": title,
            "raw_line": line,
            "line_number": line_num,
        })
    
    # Second pass: calculate end times and create Track objects
    for i, entry in enumerate(entries):
        if i + 1 < len(entries):
            end_sec = entries[i + 1]["start"]
        else:
            end_sec = audio_duration if audio_duration > 0 else 0
        
        song = Track(
            index=i + 1,
            start_seconds=entry["start"],
            end_seconds=end_sec,
            title=entry["title"],
            raw_line=entry["raw_line"],
            line_number=entry["line_number"],
        )
        songs.append(song)
    
    return songs

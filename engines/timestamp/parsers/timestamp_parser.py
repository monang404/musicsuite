import re
from engines.timestamp.utils import clean_title, time_to_seconds
from engines.timestamp.models.track import Track

class TimestampParser:
    """
    Combined utility for parsing timestamps from various text formats.
    """

    @staticmethod
    def parse_from_text(text: str) -> list[dict]:
        """
        Extract timestamp entries from arbitrary text (description / comment).
        Returns list of {"seconds": int, "title": str}, sorted by time.
        """
        results = {}

        # Pattern 1: "00:15 - Title" or "00:15 | Title" or "00:15. Title"
        pattern = re.compile(
            r"""
            (?:^|[\s\-–—►•\[\(])
            (\d{1,2}:\d{2}(?::\d{2})?)   # timestamp
            [\s\-–—|\.]+                  # separator
            (.+?)                         # title
            (?:\s*$)
            """,
            re.VERBOSE | re.MULTILINE,
        )

        # Pattern 2: YouTube native "00:15 Title" (space only)
        pattern2 = re.compile(
            r"^(\d{1,2}:\d{2}(?::\d{2})?)\s{1,3}(.+)$",
            re.MULTILINE,
        )

        for pat in [pattern, pattern2]:
            for m in pat.finditer(text):
                time_str = m.group(1).strip()
                title = clean_title(m.group(2))
                if not title or len(title) < 2:
                    continue
                try:
                    secs = time_to_seconds(time_str)
                except (ValueError, IndexError):
                    continue
                if secs not in results:
                    results[secs] = {"seconds": secs, "title": title}

        entries = sorted(results.values(), key=lambda x: x["seconds"])
        return entries

    @staticmethod
    def parse_formatted(text: str, audio_duration: int = 0) -> list[Track]:
        """
        Parse timestamp text in MM:SS|Title format into Track objects.
        """
        songs = []
        lines = text.strip().split("\n")
        
        entries = []
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
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

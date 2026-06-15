import re


class AutoTimestampError(Exception):
    """Raised when all methods fail. Message shown to user."""
    pass


def seconds_to_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def time_to_seconds(t: str) -> int:
    parts = list(map(int, t.strip().split(":")))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def clean_title(title: str) -> str:
    title = title.strip(" -–—|•►●▶◆★♪♫")
    title = re.sub(r"\s*https?://\S+", "", title)
    title = re.sub(r"\s{2,}", " ", title)
    return title.strip()


def entries_to_text(entries: list[dict]) -> str:
    """Convert list of {seconds, title} to MM:SS|Title text."""
    lines = []
    for e in entries:
        lines.append(f"{seconds_to_time(e['seconds'])}|{e['title']}")
    return "\n".join(lines)

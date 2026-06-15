from engines.timestamp.utils import clean_title

def extract_chapters(info: dict) -> list[dict] | None:
    """Extract from yt-dlp 'chapters' field."""
    chapters = info.get("chapters") or []
    if len(chapters) < 2:
        return None

    entries = []
    for ch in chapters:
        start = int(ch.get("start_time", 0))
        title = clean_title(ch.get("title", ""))
        if title:
            entries.append({"seconds": start, "title": title})

    return entries if len(entries) >= 2 else None

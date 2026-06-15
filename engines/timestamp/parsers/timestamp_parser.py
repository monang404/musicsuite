import re
from engines.timestamp.utils import clean_title, time_to_seconds

def parse_timestamps_from_text(text: str) -> list[dict]:
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

import re

def extract_titles_from_text(text: str, video_title: str = "") -> list[str]:
    """
    Extract a list of song titles (without timestamps) from description/OCR text.
    Looks for numbered lines or lines containing artist - title separators,
    with relaxed rules for OCR text.
    """
    titles = []
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    
    # Pre-clean video title and potential artist names for comparison
    video_title_clean = re.sub(r'[^a-zA-Z0-9]', '', video_title.lower()) if video_title else ""
    
    NUMBERING_PATTERN = re.compile(r"^\s*\[?[a-zA-Z0-9]{1,2}\]?[\s\.\-–—\)]+")

    candidates = []
    numbered_count = 0
    
    for line in lines:
        if line.startswith("#") or "http://" in line or "https://" in line:
            continue
            
        # Skip lines containing timestamps (handled by regular parser)
        if re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", line):
            continue
            
        # Clean numbering patterns: "1. Title", "01. Title", "n. Title", etc.
        cleaned = re.sub(r"^\s*\[?[a-zA-Z0-9]{1,2}\]?[\s\.\-–—\)]+", "", line).strip()
        cleaned = cleaned.strip(" -–—|•►●▶◆★♪♫\"'")
        
        # Skip very short or overly long lines, or numbers only
        if not cleaned or len(cleaned) < 3 or len(cleaned) > 80 or cleaned.isdigit():
            continue
            
        # Skip if it's just the video title / channel header (e.g. SEVENTEEN)
        # We check if the line is a substring of the video title and is short
        cleaned_lower = cleaned.lower()
        cleaned_alnum = re.sub(r'[^a-zA-Z0-9]', '', cleaned_lower)
        if len(cleaned_alnum) >= 3 and video_title_clean:
            if cleaned_alnum == video_title_clean:
                continue
            if len(cleaned_alnum) < 15 and cleaned_alnum in video_title_clean:
                if cleaned_lower in ["seventeen", "album", "full album", "best of", "hits", "kumpulan", "lagu"]:
                    continue

        is_numbered = NUMBERING_PATTERN.match(line) is not None
        has_separator = any(sep in cleaned for sep in [" - ", " – ", " — ", " | ", " : "])
        
        # Skip generic marketing/mood words (like "sedih", "patah", "viral", "like") if they have no numbering/separator
        if not is_numbered and not has_separator:
            if " " not in cleaned:
                cleaned_lower = cleaned.lower()
                cleaned_alnum = re.sub(r'[^a-zA-Z0-9]', '', cleaned_lower)
                video_words = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in video_title.split()] if video_title else []
                is_video_word = cleaned_alnum in video_words
                generic_words = {
                    "sedih", "patah", "viral", "like", "subscribe", "hits", "terbaru", "populer", 
                    "lagu", "sad", "love", "album", "cover", "music", "best", "paling", "enak", 
                    "mantap", "syahdu", "galau", "rindu", "cinta", "hati", "dan", "yang", "new", 
                    "top", "trending", "indo", "malaysia", "share"
                }
                is_generic = cleaned_alnum in generic_words
                if is_video_word or is_generic:
                    continue

        candidates.append({
            "original": line,
            "cleaned": cleaned,
            "is_numbered": is_numbered,
            "has_separator": has_separator
        })
        if is_numbered:
            numbered_count += 1

    # Relax rule if we have numbering or separators
    is_likely_tracklist = numbered_count >= 2 or (len(candidates) >= 3 and any(c["has_separator"] for c in candidates))

    # Identify bounds of actual tracklist items (to filter out header/footer unnumbered junk)
    first_marker_idx = None
    last_marker_idx = None
    for idx, c in enumerate(candidates):
        if c["is_numbered"] or c["has_separator"]:
            if first_marker_idx is None:
                first_marker_idx = idx
            last_marker_idx = idx

    for idx, c in enumerate(candidates):
        if is_likely_tracklist:
            # If it has numbering or separator, always keep it
            if c["is_numbered"] or c["has_separator"]:
                titles.append(c["cleaned"])
            # If it's unnumbered, keep it only if it is positioned between first and last marker
            elif first_marker_idx is not None and last_marker_idx is not None and first_marker_idx < idx < last_marker_idx:
                titles.append(c["cleaned"])
        else:
            if c["is_numbered"] or c["has_separator"]:
                titles.append(c["cleaned"])
                
    return titles

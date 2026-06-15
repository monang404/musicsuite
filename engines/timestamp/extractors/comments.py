from engines.timestamp.parsers.timestamp_parser import TimestampParser
from engines.timestamp.parsers.title_parser import extract_titles_from_text

def extract_comment_timestamps(url: str) -> list[dict] | None:
    """
    Fetch top 30 comments via yt-dlp and look for tracklist.
    Returns the best comment's parsed timestamps, or None.
    """
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "getcomments": True,
            "extractor_args": {
                "youtube": {"max_comments": ["30", "all", "0", "0"]}
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        comments = info.get("comments") or []
        if not comments:
            return None

        # Sort by like_count descending — pinned/popular comments first
        comments.sort(key=lambda c: c.get("like_count") or 0, reverse=True)

        best_entries = None
        best_count = 1  # minimum 2 timestamps to qualify

        for comment in comments[:30]:
            text = comment.get("text") or ""
            entries = TimestampParser.parse_from_text(text)
            if len(entries) > best_count:
                best_count = len(entries)
                best_entries = entries

        return best_entries

    except Exception:
        return None


def extract_titles_from_comments(url: str, video_title: str = "") -> list[str]:
    """
    Fetch top 30 comments and extract list of song titles (without timestamps).
    """
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "getcomments": True,
            "extractor_args": {
                "youtube": {"max_comments": ["30", "all", "0", "0"]}
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        comments = info.get("comments") or []
        if not comments:
            return []

        # Sort comments by like count descending
        comments.sort(key=lambda c: c.get("like_count") or 0, reverse=True)

        best_titles = []
        best_count = 1  # minimum 2 titles

        for comment in comments[:30]:
            text = comment.get("text") or ""
            titles = extract_titles_from_text(text, video_title)
            if len(titles) > best_count:
                best_count = len(titles)
                best_titles = titles

        return best_titles

    except Exception:
        return []

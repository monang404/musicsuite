import re
from typing import List, Tuple
from engines.search.models.playlist_source import PlaylistSource
from engines.search.ranking.shared_patterns import HARD_EXCLUDE_PATTERNS

# ── Existing auto-generated noise patterns ────────────────────────────────────
AUTO_GENERATED_PATTERNS = [
    r"^mix\s*-",
    r"\bradio\b",
    r"^mix$",
]

# ── NEW: Non-music hard reject — TV dramas, religious, educational, gaming ────
# These patterns should always discard regardless of artist query.
NON_MUSIC_HARD_REJECT_PATTERNS = [
    # Indonesian TV / drama
    r"\bfull\s+episodes?\b",
    r"\bseason\s+\d",
    r"\bsinetron\b",
    r"\bdrama\b",
    r"\bserial\b",
    r"\bsoap\s+opera\b",
    # Indonesian-specific TV shows embedded in title
    r"\bamanah\s+wali\b",
    r"\bwali\s+songo\b",
    r"\bwali\s+paidi\b",
    r"\bwali\s+hakim\b",
    r"\bpengantin\s+wali\b",
    r"\bwali\s+kota\b",
    r"\bwali\s+murid\b",
    r"\bwali\s+nikah\b",
    # Religious / educational
    r"\bkajian\b",
    r"\bceramah\b",
    r"\btausiyah\b",
    # Podcasts
    r"\bpodcast\b",
    # Gaming
    r"\bgameplay\b",
    r"\bwalkthrough\b",
    # Soap operas common pattern: "Episode 1 - 566"
    r"episode\s+\d+\s*[-–to]+\s*\d+",
]


def _explain_filter_exclusion(pl: PlaylistSource) -> str:
    """
    Returns (human-readable reason, stage) if the playlist should be excluded,
    or ("", "") if it passes.
    """
    lower = pl.title.lower()
    for pat in HARD_EXCLUDE_PATTERNS:
        if re.search(pat, lower):
            return f"HARD_EXCLUDE: pattern '{pat}' matched title"
    for pat in AUTO_GENERATED_PATTERNS:
        if re.search(pat, lower):
            return f"AUTO_GEN: pattern '{pat}' matched title"
    for pat in NON_MUSIC_HARD_REJECT_PATTERNS:
        if re.search(pat, lower):
            return f"NON_MUSIC: pattern '{pat}' matched title"
    if pl.item_count > 0 and pl.item_count < 3:
        return f"TOO_FEW_ITEMS: item_count={pl.item_count}"
    return ""


class PlaylistFilter:
    def should_exclude(self, title: str) -> bool:
        lower_title = title.lower()
        for pattern in HARD_EXCLUDE_PATTERNS:
            if re.search(pattern, lower_title):
                return True
        for pattern in AUTO_GENERATED_PATTERNS:
            if re.search(pattern, lower_title):
                return True
        for pattern in NON_MUSIC_HARD_REJECT_PATTERNS:
            if re.search(pattern, lower_title):
                return True
        return False

    def apply(self, playlists: List[PlaylistSource]) -> List[PlaylistSource]:
        filtered = []
        for pl in playlists:
            reason = _explain_filter_exclusion(pl)
            if reason:
                pl.reject_reason = reason
                continue

            pl.soft_penalty = 0
            filtered.append(pl)
        return filtered

    def explain(self, playlists: List[PlaylistSource]) -> List[Tuple[PlaylistSource, str]]:
        """
        Returns a list of (playlist, reject_reason) for ALL playlists.
        Empty string means PASS.
        """
        results = []
        for pl in playlists:
            reason = _explain_filter_exclusion(pl)
            results.append((pl, reason))
        return results

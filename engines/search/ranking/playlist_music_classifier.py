"""
PlaylistMusicClassifier

Analyses playlist metadata (title, channel, and sample entry titles) to compute
a music_score in [0.0, 1.0] that reflects how likely the playlist is a *music*
playlist (as opposed to TV drama, religious content, podcasts, etc.).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict

# ---------------------------------------------------------------------------
# Signal tables
# ---------------------------------------------------------------------------

# Each positive keyword contributes a fixed weight to the raw score.
POSITIVE_TITLE_SIGNALS: Dict[str, float] = {
    "full album":     0.30,
    "greatest hits":  0.25,
    "best songs":     0.20,
    "best of":        0.20,
    "discography":    0.25,
    "official music": 0.20,
    "music video":    0.18,
    "nonstop":        0.15,
    "album":          0.15,
    "hits":           0.12,
    "songs":          0.12,
    "playlist":       0.10,
    "music":          0.10,
    "official":       0.10,
    "topic":          0.10,  # YouTube auto-generated "Artist - Topic" channel
    "- topic":        0.45,  # Strong topic signal in title
    "band":           0.08,
    "single":         0.08,
    "mix":            0.06,  # weak positive — mix playlists can be music
}

POSITIVE_CHANNEL_SIGNALS: Dict[str, float] = {
    "- topic":        0.35,   # strong: YouTube official artist topic channel
    "official":       0.20,
    "music":          0.15,
    "records":        0.12,
    "entertainment":  0.08,
    "vevo":           0.20,
}

# Negative keywords — reduce the raw positive score.
NEGATIVE_TITLE_SIGNALS: Dict[str, float] = {
    # TV / Drama
    "full episode":   0.90,
    "full episodes":  0.90,
    "episode":        0.60,
    "eps":            0.40,
    "season":         0.60,
    "series":         0.40,
    "sinetron":       0.85,
    "drama":          0.70,
    "serial":         0.70,
    "soap opera":     0.80,
    # Indonesian specific TV / religious
    "amanah wali":    0.95,
    "wali songo":     0.95,
    "pengantin wali": 0.90,
    "wali paidi":     0.90,
    "wali hakim":     0.90,
    "kajian":         0.85,
    "ceramah":        0.85,
    "tausiyah":       0.85,
    # Podcasts / Talk shows
    "podcast":        0.80,
    "curhat":         0.60,
    "talk show":      0.70,
    "interview":      0.65,
    # Educational
    "tutorial":       0.60,
    "course":         0.55,
    "class":          0.40,
    "lesson":         0.50,
    # Gaming
    "gameplay":       0.70,
    "gaming":         0.65,
    "walkthrough":    0.65,
    # Other non-music
    "movie":          0.50,
    "film":           0.40,  # "Film Favorit" by Sheila on 7 is music so keep low
    "documentary":    0.65,
    "news":           0.55,
    "berita":         0.55,
}

NEGATIVE_CHANNEL_SIGNALS: Dict[str, float] = {
    "tv":             0.30,
    "channel tv":     0.50,
    "official film":  0.40,
    "gaming":         0.60,
    "podcast":        0.55,
}

# Entry title signals — used when sample entry titles are available
ENTRY_MUSIC_PATTERNS = [
    r"\bofficial\b",
    r"\blyric[s]?\b",
    r"\bmusic video\b",
    r"\bmv\b",
    r"\bft\.?\b",
    r"\bfeat\.?\b",
    r"\(official\)",
    r"\[official\]",
    r"\bband\b",
    r"\balbum\b",
]

ENTRY_NON_MUSIC_PATTERNS = [
    r"\bepisode\b",
    r"\beps?\b\s*\d",
    r"\bseason\b",
    r"\bpart\b\s*\d",
    r"\bfull\s+movie\b",
]


@dataclass
class PlaylistMusicScore:
    """Result of music classification."""
    music_score: float          # 0.0 – 1.0
    signals: Dict[str, float] = field(default_factory=dict)
    # Explanation string for debug reporter
    note: str = ""


class PlaylistMusicClassifier:
    """
    Classifies whether a playlist is a music playlist.

    Usage
    -----
    clf = PlaylistMusicClassifier()
    result = clf.classify(title, channel, entry_titles)
    print(result.music_score)  # 0.0 – 1.0
    """

    def classify(
        self,
        title: str,
        channel: str,
        entry_titles: List[str] = None,
    ) -> PlaylistMusicScore:
        title_lower = title.lower().strip()
        channel_lower = channel.lower().strip()
        entry_titles = [t for t in (entry_titles or []) if t]

        signals: Dict[str, float] = {}

        # ---- Positive signals -----------------------------------------------
        pos_raw = 0.0
        for kw, weight in POSITIVE_TITLE_SIGNALS.items():
            if kw in title_lower:
                signals[f"title:+{kw}"] = weight
                pos_raw += weight

        for kw, weight in POSITIVE_CHANNEL_SIGNALS.items():
            if kw in channel_lower:
                signals[f"channel:+{kw}"] = weight
                pos_raw += weight

        # Entry title analysis
        if entry_titles:
            music_count = sum(
                1 for t in entry_titles
                if any(re.search(p, t.lower()) for p in ENTRY_MUSIC_PATTERNS)
            )
            non_music_count = sum(
                1 for t in entry_titles
                if any(re.search(p, t.lower()) for p in ENTRY_NON_MUSIC_PATTERNS)
            )
            total = len(entry_titles)
            if total > 0:
                music_ratio = music_count / total
                non_music_ratio = non_music_count / total
                entry_bonus = music_ratio * 0.30
                entry_penalty = non_music_ratio * 0.50
                signals["entries:music_ratio"] = entry_bonus
                signals["entries:non_music_penalty"] = -entry_penalty
                pos_raw += entry_bonus - entry_penalty

        # ---- Negative signals -----------------------------------------------
        neg_factor = 0.0
        for kw, penalty in NEGATIVE_TITLE_SIGNALS.items():
            if kw in title_lower:
                signals[f"title:-{kw}"] = -penalty
                neg_factor = max(neg_factor, penalty)

        for kw, penalty in NEGATIVE_CHANNEL_SIGNALS.items():
            if kw in channel_lower:
                signals[f"channel:-{kw}"] = -penalty
                neg_factor = max(neg_factor, penalty * 0.5)

        # ---- Combine ---------------------------------------------------------
        # If a strong negative signal fires, suppress the positive score
        effective_pos = max(0.0, pos_raw)
        music_score = effective_pos * (1.0 - neg_factor)
        music_score = max(0.0, min(1.0, music_score))

        # Build a note
        top_pos = sorted(
            [(k, v) for k, v in signals.items() if v > 0],
            key=lambda x: -x[1],
        )[:3]
        top_neg = sorted(
            [(k, v) for k, v in signals.items() if v < 0],
            key=lambda x: x[1],
        )[:2]
        note_parts = [f"{k}={v:+.2f}" for k, v in top_pos + top_neg]
        note = ", ".join(note_parts) if note_parts else "no signals"

        return PlaylistMusicScore(
            music_score=round(music_score, 4),
            signals=signals,
            note=note,
        )

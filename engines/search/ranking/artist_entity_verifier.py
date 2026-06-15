"""
ArtistEntityVerifier

Verifies whether a playlist belongs to the searched music artist, rather than
just sharing a token with the artist's name.

Returns an ArtistConfidence in [0.0, 1.0].
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict


# ---------------------------------------------------------------------------
# Non-music context phrases — if these appear in the title alongside the artist
# token, the playlist almost certainly is NOT about the music artist.
# ---------------------------------------------------------------------------
NON_MUSIC_CONTEXT_PHRASES = [
    "amanah wali",
    "wali songo",
    "wali paidi",
    "wali hakim",
    "pengantin wali",
    "wali kota",
    "wali murid",
    "wali class",
    "wali nikah",
    "wali santri",
    # Generic non-music
    "episode",
    "full episode",
    "season",
    "sinetron",
    "drama",
    "ceramah",
    "kajian",
    "podcast",
    "tutorial",
    "gameplay",
    "gaming",
]

# Phrases that strengthen the case that it IS the music artist
MUSIC_CONTEXT_PHRASES = [
    "official music",
    "music video",
    "full album",
    "greatest hits",
    "best songs",
    "best of",
    "discography",
    "official playlist",
    "top songs",
    "hits",
    "album",
    "nonstop",
    "songs",
]


@dataclass
class ArtistConfidence:
    """Result of artist entity verification."""
    score: float            # 0.0 – 1.0
    reason: str = ""
    signals: Dict[str, float] = field(default_factory=dict)


class ArtistEntityVerifier:
    """
    Checks how confidently a playlist belongs to a specific music artist.

    Usage
    -----
    verifier = ArtistEntityVerifier()
    result = verifier.verify(
        artist_query="wali",
        playlist_title="Wali - Topic",
        playlist_channel="Wali - Topic",
        sample_entry_titles=["Cari Jodoh", "Baik Baik Sayang", ...],
    )
    print(result.score)  # e.g. 0.95
    """

    def verify(
        self,
        artist_query: str,
        playlist_title: str,
        playlist_channel: str,
        sample_entry_titles: List[str] = None,
    ) -> ArtistConfidence:
        if not artist_query:
            return ArtistConfidence(score=0.5, reason="no artist query provided")

        artist_lower = artist_query.lower().strip()
        title_lower = playlist_title.lower().strip()
        channel_lower = playlist_channel.lower().strip()
        sample_entry_titles = [t for t in (sample_entry_titles or []) if t]

        signals: Dict[str, float] = {}
        reasons: List[str] = []

        # ---- Hard disqualification check ------------------------------------
        for phrase in NON_MUSIC_CONTEXT_PHRASES:
            if phrase in title_lower:
                signals[f"hard_reject:{phrase}"] = -1.0
                return ArtistConfidence(
                    score=0.0,
                    reason=f"Hard rejected: title contains non-music phrase '{phrase}'",
                    signals=signals,
                )

        # ---- Positive signals -----------------------------------------------

        # 1. Artist name appears as a whole word in the playlist title
        artist_in_title = self._word_in_text(artist_lower, title_lower)
        if artist_in_title:
            signals["artist_in_title"] = 0.40
            reasons.append("artist name in playlist title")
        else:
            signals["artist_in_title"] = 0.0

        # 2. Artist name in channel
        artist_in_channel = self._word_in_text(artist_lower, channel_lower)
        if artist_in_channel:
            signals["artist_in_channel"] = 0.30
            reasons.append("artist name in channel")
        else:
            signals["artist_in_channel"] = 0.0

        # 3. Official "- Topic" channel — YouTube auto-generated artist channel
        is_topic_channel = "- topic" in channel_lower or "- topic" in title_lower
        if is_topic_channel:
            signals["topic_channel"] = 0.50
            reasons.append("YouTube Topic channel")
        else:
            signals["topic_channel"] = 0.0

        # 4. Music context in title
        music_ctx_score = 0.0
        for phrase in MUSIC_CONTEXT_PHRASES:
            if phrase in title_lower:
                music_ctx_score = 0.10
                reasons.append(f"music context: '{phrase}'")
                break
        signals["music_context"] = music_ctx_score

        # 5. Sample entry title analysis
        if sample_entry_titles:
            artist_hit = sum(
                1 for t in sample_entry_titles
                if self._word_in_text(artist_lower, t.lower())
            )
            ratio = artist_hit / len(sample_entry_titles)
            entry_score = ratio * 0.30
            signals["entry_artist_ratio"] = entry_score
            if ratio >= 0.5:
                reasons.append(f"{artist_hit}/{len(sample_entry_titles)} entries mention artist")
        else:
            signals["entry_artist_ratio"] = 0.0

        # ---- Compute raw score ----------------------------------------------
        raw = sum(signals.values())
        score = max(0.0, min(1.0, raw))

        # If artist is not in title at all AND not in channel → cap at 0.20
        # (token might appear in an entry but that's not enough alone)
        if not artist_in_title and not artist_in_channel and not is_topic_channel:
            score = min(score, 0.20)
            reasons.append("artist not in title or channel — capped at 0.20")

        reason_str = "; ".join(reasons) if reasons else "no matching signals"
        return ArtistConfidence(
            score=round(score, 4),
            reason=reason_str,
            signals=signals,
        )

    def _word_in_text(self, word: str, text: str) -> bool:
        """
        Returns True if `word` appears as a whole-word match in `text`.
        Handles multi-word artist names (e.g. 'sheila on 7', 'dewa 19').
        """
        if not word:
            return False
        # Escape regex special chars in the word
        escaped = re.escape(word)
        # For multi-word queries just check substring (whole-word boundary
        # on the first and last token is sufficient)
        if " " in word:
            return bool(re.search(r"\b" + escaped + r"\b", text))
        return bool(re.search(r"\b" + escaped + r"\b", text))

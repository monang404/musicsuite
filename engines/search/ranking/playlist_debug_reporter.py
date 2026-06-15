"""
PlaylistDebugReporter

Produces human-readable per-candidate score breakdowns for debugging.
Used by debug_playlist_pipeline.py and can be enabled in service.py.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CandidateReport:
    title: str
    url: str
    music_score: float
    artist_confidence: float
    metadata_quality: float
    size_score: float
    final_score: float
    status: str          # "ACCEPT" | "REJECT"
    reject_reason: str = ""
    # raw signal notes
    music_signals_note: str = ""
    artist_signals_note: str = ""


class PlaylistDebugReporter:
    """
    Formats per-candidate score breakdown in a readable block.

    Example output
    --------------
    ─────────────────────────────────────────────────
    Title          : Wali Hits Vol.1
    Music Score    : 0.92
    Artist Confid. : 0.97
    Metadata Qual. : 0.81
    Size Score     : 0.75
    Final Score    : 0.93
    Status         : ACCEPT
    ─────────────────────────────────────────────────
    """

    def format_candidate(self, r: CandidateReport) -> str:
        sep = "-" * 51
        lines = [
            sep,
            f"  Title          : {r.title}",
            f"  URL            : {r.url[:70]}",
            f"  Music Score    : {r.music_score:.2f}",
            f"  Artist Confid. : {r.artist_confidence:.2f}",
            f"  Metadata Qual. : {r.metadata_quality:.2f}",
            f"  Size Score     : {r.size_score:.2f}",
            f"  Final Score    : {r.final_score:.2f}",
            f"  Status         : {r.status}",
        ]
        if r.reject_reason:
            lines.append(f"  Reason         : {r.reject_reason}")
        if r.music_signals_note:
            lines.append(f"  Music signals  : {r.music_signals_note}")
        if r.artist_signals_note:
            lines.append(f"  Artist signals : {r.artist_signals_note}")
        lines.append(sep)
        return "\n".join(lines)

    def format_all(self, reports: List[CandidateReport]) -> str:
        return "\n".join(self.format_candidate(r) for r in reports)

    def to_markdown_table(self, reports: List[CandidateReport]) -> str:
        header = (
            "| Title | Music | Artist | Metadata | Size | Final | Status | Reason |\n"
            "|-------|-------|--------|----------|------|-------|--------|--------|"
        )
        rows = []
        for r in reports:
            reason = r.reject_reason or "—"
            rows.append(
                f"| {r.title[:45]} | {r.music_score:.2f} | {r.artist_confidence:.2f} "
                f"| {r.metadata_quality:.2f} | {r.size_score:.2f} | {r.final_score:.2f} "
                f"| {r.status} | {reason[:40]} |"
            )
        return header + "\n" + "\n".join(rows)

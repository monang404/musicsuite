import re
from typing import List
from engines.search.models.compilation_source import CompilationVideo
from engines.search.ranking.shared_patterns import HARD_EXCLUDE_PATTERNS

SOFT_PENALTIES = {
    r'\blive\b':         15,
    r'\bcover\b':        10,
    r'\bremix\b':        10,
    r'\bslowed\b':       20,
    r'\breverb\b':       20,
    r'\bunofficial\b':    5,
}

class CompilationFilter:
    def should_exclude(self, title: str) -> bool:
        lower_title = title.lower()
        for pattern in HARD_EXCLUDE_PATTERNS:
            if re.search(pattern, lower_title):
                return True
        return False

    def compute_penalty(self, title: str) -> int:
        lower_title = title.lower()
        total_penalty = 0
        for pattern, penalty in SOFT_PENALTIES.items():
            if re.search(pattern, lower_title):
                total_penalty += penalty
        return total_penalty

    def apply(self, sources: List[CompilationVideo]) -> List[CompilationVideo]:
        filtered = []
        album_keywords = ['album', 'kompilasi', 'greatest hits', 'best of']
        for source in sources:
            if self.should_exclude(source.title):
                continue
                
            # Pre-filtering Durasi: Drop short videos claiming to be albums
            lower_title = source.title.lower()
            is_album_claim = any(k in lower_title for k in album_keywords)
            if is_album_claim and source.duration and source.duration < 600:
                continue # Skip video < 10 mins claiming to be full album
                
            source.soft_penalty = self.compute_penalty(source.title)
            filtered.append(source)
        return filtered

CompilationFilter = CompilationFilter

import re
from typing import List

QUERY_TEMPLATES = [
    "{artist} full album timestamp",
    "{artist} greatest hits timestamp",
    "{artist} best songs timestamp",
    "{artist} kompilasi terbaik",
    "{artist} full album tracklist",
    "{artist} best songs tracklist",
    "{artist} discography",
    "{artist} live performance",
    "{artist} essential tracks",
    "{artist} full album",
]

PLAYLIST_QUERY_TEMPLATES = [
    "{artist} playlist",
    "{artist} official playlist",
    "{artist} mix",
]

class QueryExpander:
    def expand(self, artist: str, count: int = 5) -> List[str]:
        normalized_artist = self._normalize(artist)
        if not normalized_artist:
            return []
            
        queries = []
        for template in QUERY_TEMPLATES:
            queries.append(template.format(artist=normalized_artist))
            
        return queries[:count]

    def expand_playlist(self, artist: str, count: int = 7) -> List[str]:
        normalized_artist = self._normalize(artist)
        if not normalized_artist:
            return []
            
        queries = []
        for template in PLAYLIST_QUERY_TEMPLATES:
            queries.append(template.format(artist=normalized_artist))
            
        return queries[:count]

    def _normalize(self, raw: str) -> str:
        name = raw.strip()
        name = re.sub(r'\s+', ' ', name)
        return name

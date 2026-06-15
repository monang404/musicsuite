import re
from typing import List

QUERY_TEMPLATES = [
    "{artist} full album timestamp",
    "{artist} greatest hits timestamp",
    "{artist} best songs timestamp",
    "{artist} full album tracklist",
    "{artist} kompilasi terbaik",
    "{artist} discography",
    "{artist} greatest hits",
    "{artist} best songs",
    "{artist} full album",
    "{artist} top songs",
    "{artist} all songs nonstop",
    "{artist} lagu terbaik",
    "{artist} best songs tracklist",
    "{artist} live performance",
    "{artist} essential tracks",
]

PLAYLIST_QUERY_TEMPLATES = [
    "{artist} playlist",
    "{artist} official playlist",
    "{artist} mix",
    "{artist} songs playlist",
    "{artist} topic",
]

class QueryExpander:
    def expand(self, artist: str, count: int = 8) -> List[str]:
        normalized_artist = self._normalize(artist)
        if not normalized_artist:
            return []
            
        queries = []
        for template in QUERY_TEMPLATES:
            queries.append(template.format(artist=normalized_artist))
            
        return queries[:count]

    def expand_playlist(self, artist: str, count: int = 5) -> List[str]:
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

import subprocess
import json
from services.security import validate_url
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

from engines.search.providers.base_provider import BaseProvider, ProviderUnavailableError
from engines.search.models.compilation_source import CompilationVideo
from engines.search.models.playlist_source import PlaylistSource
from engines.search.models.search_entity import SearchEntity
from engines.search.metadata.chapter_parser import ChapterParser
from engines.search.metadata.timestamp_parser import TimestampParser
from engines.search.metadata.tracklist_builder import TracklistBuilder

class YtdlpProvider(BaseProvider):
    def __init__(self):
        if not self._check_ytdlp_available():
            raise ProviderUnavailableError("yt-dlp tidak ditemukan. Pastikan yt-dlp sudah terinstall di PATH.")
        
        self.chapter_parser = ChapterParser()
        self.timestamp_parser = TimestampParser()
        self.tracklist_builder = TracklistBuilder()

    def _check_ytdlp_available(self) -> bool:
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True, timeout=5, text=True,
                shell=False
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def search_fast(self, queries: List[str], result_count: int = 15) -> List[CompilationVideo]:
        """
        Jalankan semua query secara paralel.
        Max 4 worker threads.
        Timeout per query: 8 detik.
        result_count: jumlah hasil per query (default 15).
        """
        all_sources = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_query = {executor.submit(self._search_single, q, result_count): q for q in queries}
            
            for future in as_completed(future_to_query):
                try:
                    sources = future.result()
                    all_sources.extend(sources)
                except Exception as e:
                    # Log error but continue with other queries
                    logger.error(f"Error searching for query {future_to_query[future]}: {e}")
                    pass

        return self._deduplicate(all_sources)

    def _search_single(self, query: str, result_count: int = 15) -> List[CompilationVideo]:
        cmd = [
            "yt-dlp",
            f"ytsearch{result_count}:{query}",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--ignore-errors",
            "--socket-timeout", "15"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45, shell=False) # giving extra time for subprocess overhead
        except subprocess.TimeoutExpired:
            return []

        sources = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                sources.append(CompilationVideo.from_ytdlp_info(data))
            except json.JSONDecodeError:
                pass
        
        return sources

    def fetch_full(self, url: str) -> CompilationVideo:
        """
        Fetch metadata lengkap: chapters, full description.
        Timeout: 12 detik.
        """
        validate_url(url)
        cmd = [
            "yt-dlp",
            url,
            "--dump-json",
            "--no-warnings",
            "--ignore-errors",
            "--socket-timeout", "15",
            "--skip-download"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Timeout fetching metadata for {url}")
            
        if result.returncode != 0 and not result.stdout.strip():
            raise RuntimeError(f"Failed to fetch metadata for {url}: {result.stderr}")

        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON returned by yt-dlp for {url}")

        source = CompilationVideo.from_ytdlp_info(data)
        source.is_deep_fetched = True
        
        description = data.get('description', '')
        raw_chapters = data.get('chapters')
        
        # Parse Tracklist
        chapter_res = self.chapter_parser.parse(raw_chapters, source.duration)
        timestamp_res = self.timestamp_parser.parse(description)
        build_res = self.tracklist_builder.build(chapter_res, timestamp_res)
        
        source.has_chapters = build_res.has_chapters
        source.has_timestamps = build_res.has_timestamps
        source.chapter_count = chapter_res.chapter_count if chapter_res else 0
        source.timestamp_count = timestamp_res.timestamp_count if timestamp_res else 0
        source.track_count = build_res.track_count
        source.tracks = build_res.tracks
        
        source.chapters_cover_full_duration = build_res.chapters_cover_full_duration
        source.timestamps_are_monotonic = build_res.timestamps_are_monotonic
        
        return source

    def search_playlists(self, queries: List[str]) -> List[PlaylistSource]:
        all_playlists = []
        errors = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_query = {executor.submit(self._search_single_playlist, q): q for q in queries}
            
            for future in as_completed(future_to_query):
                try:
                    playlists = future.result()
                    all_playlists.extend(playlists)
                except Exception as e:
                    logger.exception(f"Error searching playlist for query {future_to_query[future]}")
                    errors.append(e)

        if errors and len(errors) == len(queries):
            raise Exception("Playlist search failed completely")

        return self._deduplicate_entities(all_playlists)

    def _search_single_playlist(self, query: str) -> List[PlaylistSource]:
        url = f"https://www.youtube.com/results?search_query={query}&sp=EgIQAw%253D%253D"
        cmd = [
            "yt-dlp",
            url,
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--ignore-errors",
            "--socket-timeout", "15"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35, shell=False)
        except Exception as e:
            logger.exception("Playlist search failed")
            raise

        playlists = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                ie_key = data.get('ie_key', '')
                url_field = data.get('url', data.get('webpage_url', ''))
                if ie_key == 'YoutubePlaylist' or 'list=' in url_field:
                    playlists.append(PlaylistSource.from_ytdlp_playlist_info(data))
            except json.JSONDecodeError:
                pass
        
        return playlists

    def fetch_playlist_full(self, playlist_url: str) -> PlaylistSource:
        validate_url(playlist_url)
        cmd = [
            "yt-dlp",
            playlist_url,
            "--flat-playlist",
            "--dump-single-json",
            "--no-warnings",
            "--ignore-errors",
            "--socket-timeout", "15"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Timeout fetching playlist metadata for {playlist_url}")
            
        if result.returncode != 0 and not result.stdout.strip():
            raise RuntimeError(f"Failed to fetch playlist metadata for {playlist_url}: {result.stderr}")

        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON returned by yt-dlp for {playlist_url}")

        source = PlaylistSource.from_ytdlp_playlist_info(data)
        source.is_deep_fetched = True
        
        return source

    def _deduplicate(self, sources: List[CompilationVideo]) -> List[CompilationVideo]:
        return self._deduplicate_entities(sources)

    def _deduplicate_entities(self, sources: List[Any]) -> List[Any]:
        seen_urls = set()
        result = []
        for s in sources:
            if s.url and s.url not in seen_urls:
                seen_urls.add(s.url)
                result.append(s)
        return result

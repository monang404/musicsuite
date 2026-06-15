import unittest
from engines.search.ranking.playlist_music_classifier import PlaylistMusicClassifier, PlaylistMusicScore

class TestPlaylistMusicClassifier(unittest.TestCase):
    def setUp(self):
        self.clf = PlaylistMusicClassifier()

    def test_strong_music_signals(self):
        result = self.clf.classify("Wali Hits Vol.1", "Wali - Topic")
        self.assertGreaterEqual(result.music_score, 0.4)
        self.assertIn("channel:+- topic", result.signals)

    def test_strong_negative_signals_tv_drama(self):
        result = self.clf.classify("Amanah Wali 8 Full Episode", "RCTI - Layar Drama Indonesia")
        self.assertEqual(result.music_score, 0.0)
        self.assertIn("title:-amanah wali", result.signals)

    def test_strong_negative_signals_religious(self):
        result = self.clf.classify("Kajian Wali Songo", "Ceramah Islam")
        self.assertEqual(result.music_score, 0.0)
        self.assertIn("title:-wali songo", result.signals)

    def test_entry_titles_boost(self):
        # A borderline title, but entries confirm it's music
        result = self.clf.classify(
            title="My Playlist",
            channel="User123",
            entry_titles=["Wali - Cari Jodoh (Official Music Video)", "Baik Baik Sayang (Lyric)"]
        )
        self.assertGreater(result.music_score, 0.0)
        self.assertGreater(result.signals.get("entries:music_ratio", 0.0), 0.0)

    def test_entry_titles_penalty(self):
        # Title looks like music, but entries are episodes
        result = self.clf.classify(
            title="Wali Full Album",
            channel="User123",
            entry_titles=["Episode 1", "Episode 2", "Eps 3"]
        )
        self.assertIn("entries:non_music_penalty", result.signals)

if __name__ == "__main__":
    unittest.main()

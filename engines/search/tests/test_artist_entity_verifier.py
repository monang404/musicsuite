import unittest
from engines.search.ranking.artist_entity_verifier import ArtistEntityVerifier

class TestArtistEntityVerifier(unittest.TestCase):
    def setUp(self):
        self.vrf = ArtistEntityVerifier()

    def test_artist_in_title(self):
        result = self.vrf.verify("wali", "Wali Hits Vol 1", "SomeChannel")
        self.assertGreaterEqual(result.score, 0.4)
        self.assertIn("artist_in_title", result.signals)

    def test_multi_word_artist_in_title(self):
        result = self.vrf.verify("sheila on 7", "Sheila on 7 Official Music", "Sony")
        self.assertGreaterEqual(result.score, 0.4)

    def test_topic_channel(self):
        result = self.vrf.verify("wali", "Wali", "Wali - Topic")
        self.assertGreaterEqual(result.score, 0.6)  # title(0.4) + channel(0.2) + topic(0.2)
        
    def test_hard_reject_non_music_context(self):
        # Even if 'wali' is the query, Amanah Wali is a hard reject
        result = self.vrf.verify("wali", "Amanah Wali Episode 1", "RCTI")
        self.assertEqual(result.score, 0.0)
        self.assertTrue("hard reject" in result.reason.lower())

    def test_no_artist_in_title_or_channel(self):
        # Query doesn't appear in title or channel
        result = self.vrf.verify("wali", "Indo Hits", "Music Channel")
        self.assertLessEqual(result.score, 0.2)
        
    def test_entry_title_boost(self):
        # Boost if entry titles contain the artist
        result = self.vrf.verify(
            "wali", 
            "Indo Hits", 
            "Music Channel", 
            ["Wali - Cari Jodoh", "Wali - Baik Baik Sayang"]
        )
        self.assertIn("entry_artist_ratio", result.signals)
        self.assertGreater(result.score, 0.0)

if __name__ == "__main__":
    unittest.main()

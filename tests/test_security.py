import unittest
import pytest
from services.security import validate_url

class TestSecurityURLValidation(unittest.TestCase):
    def test_allowed_urls(self):
        # Valid youtube urls
        allowed = [
            "https://youtube.com/watch?v=123",
            "http://youtube.com/watch?v=123",
            "https://www.youtube.com/watch?v=123",
            "https://m.youtube.com/watch?v=123",
            "https://youtu.be/123",
            "youtu.be/123",
            "youtube.com/watch?v=123",
            "www.youtube.com/watch?v=123",
        ]
        for url in allowed:
            try:
                validate_url(url)
            except ValueError as e:
                self.fail(f"URL '{url}' should be allowed but failed validation: {e}")

    def test_rejected_urls(self):
        # Invalid / disallowed urls
        rejected = [
            "https://google.com",
            "https://spotify.com/track/123",
            "spotify.com/track/123",
            "https://notyoutube.com",
            "https://youtube.com.attacker.com",
            "",
            None,
        ]
        for url in rejected:
            with self.assertRaises(ValueError):
                validate_url(url)

if __name__ == '__main__':
    unittest.main()

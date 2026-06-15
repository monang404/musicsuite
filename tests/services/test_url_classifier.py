import pytest
from services.url_classifier import classify_url

def test_classify_url():
    assert classify_url("https://youtube.com/watch?v=xxx&list=PLxxx") == "playlist"
    assert classify_url("https://youtube.com/watch?v=xxx") == "compilation"

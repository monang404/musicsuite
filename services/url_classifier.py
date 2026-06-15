from typing import Literal

def classify_url(url: str) -> Literal["playlist", "compilation"]:
    """Klasifikasi URL YouTube: playlist jika mengandung 'list=', selain itu video tunggal."""
    return "playlist" if "list=" in url else "compilation"

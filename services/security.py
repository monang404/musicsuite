from urllib.parse import urlparse

def validate_url(url: str) -> None:
    """
    Validates that a URL is a YouTube domain (youtube.com, youtu.be, or subdomains).
    Raises ValueError if validation fails.
    """
    if not url:
        raise ValueError("URL cannot be empty")
        
    try:
        parsed = urlparse(url)
        # Handle cases where scheme is missing (e.g. youtube.com/watch?v=...)
        if not parsed.scheme:
            # Re-parse with a default scheme so urlparse can extract hostname
            if not url.startswith("//"):
                parsed = urlparse("https://" + url)
            else:
                parsed = urlparse("https:" + url)

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Could not parse hostname from URL")
            
        hostname = hostname.lower()
        
        # Enforce allowed domains
        if hostname == "youtube.com" or hostname == "youtu.be" or hostname.endswith(".youtube.com"):
            return
            
        raise ValueError(f"Domain '{hostname}' is not allowed. Only youtube.com and youtu.be are permitted.")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid URL structure: {str(e)}")

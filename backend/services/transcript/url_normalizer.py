from urllib.parse import urlparse
from typing import Dict, Optional

class URLNormalizer:
    
    _ALLOWED_HOSTNAMES = {
        "www.youtube.com", "youtube.com", "youtu.be",
        "m.youtube.com", "music.youtube.com",
    }

    @staticmethod
    def normalize(url: str) -> Dict[str, str]:
        """
        Normalizes a YouTube URL and returns the canonical representation.
        Raises ValueError if the URL is invalid.
        """
        if not url:
            raise ValueError("empty URL")
            
        parsed = urlparse(url)
        
        if parsed.netloc not in URLNormalizer._ALLOWED_HOSTNAMES:
            raise ValueError(f"unsupported domain: {parsed.netloc}")
            
        video_id = URLNormalizer._extract_video_id(url)
        if not video_id:
            raise ValueError("missing video ID")
            
        return {
            "source": "youtube",
            "video_id": video_id
        }

    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        from urllib.parse import parse_qs
        parsed = urlparse(url)
        if parsed.netloc == "youtu.be":
            return parsed.path[1:]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        return None

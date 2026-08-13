import asyncio
import os
from yt_dlp import YoutubeDL
from typing import Dict, Any


class MetadataService:
    """
    Safely interfaces with yt-dlp to verify the video is ACCESSIBLE
    and retrieves metadata.
    """

    @staticmethod
    async def fetch_metadata(url: str) -> Dict[str, Any]:
        base_ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }

        def _fetch(opts):
            with YoutubeDL(opts) as ydl:
                # This will raise exceptions if the video is DELETED, PRIVATE,
                # or RESTRICTED
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "duration_seconds": info.get("duration", 0),
                    "thumbnail": info.get("thumbnail"),
                    "channel_name": info.get("uploader"),
                    "status": "ACCESSIBLE"
                }

        try:
            return await asyncio.to_thread(_fetch, base_ydl_opts)
        except Exception:
            # Fallback for bot protection
            if os.path.exists("/.dockerenv"):
                raise Exception("youtube_bot_protection")
            try:
                opts = dict(base_ydl_opts)
                opts['cookiesfrombrowser'] = ('chrome',)
                return await asyncio.to_thread(_fetch, opts)
            except Exception as inner_e:
                raise Exception(f"ACCESS_DENIED: {str(inner_e)}")

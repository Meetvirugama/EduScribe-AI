import os
import asyncio
from urllib.parse import urlparse
from yt_dlp import YoutubeDL
from fastapi import HTTPException
from core.config import settings

class YouTubeService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    def validate_url(self, url: str):
        parsed = urlparse(url)
        # HIGH-005: Keep in sync with YoutubeRequest._YOUTUBE_HOSTNAMES in schemas/video.py
        _ALLOWED_HOSTNAMES = {
            "www.youtube.com", "youtube.com", "youtu.be",
            "m.youtube.com", "music.youtube.com",
        }
        if parsed.netloc not in _ALLOWED_HOSTNAMES:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    async def fetch_metadata(self, url: str) -> dict:
        self.validate_url(url)
        
        base_ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }
        def _fetch(ydl_opts_custom):
            with YoutubeDL(ydl_opts_custom) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "duration_seconds": info.get("duration", 0),
                    "thumbnail": info.get("thumbnail"),
                    "channel_name": info.get("uploader")
                }
        try:
            return await asyncio.to_thread(_fetch, base_ydl_opts)
        except Exception:
            # Fallback to cookies if metadata fetch is blocked (ISSUE-021)
            if os.path.exists("/.dockerenv"):
                raise Exception("youtube_bot_protection")
            opts = dict(base_ydl_opts)
            opts['cookiesfrombrowser'] = ('chrome',)
            return await asyncio.to_thread(_fetch, opts)

    async def download_video(self, url: str, video_id: str) -> dict:
        self.validate_url(url)
        
        base_ydl_opts = {
            # CRITICAL-005: Request a proper video+audio stream so cv2.VideoCapture
            # can open the file for the vision pipeline (frame extraction, OCR).
            # The previous audio-only format caused the entire vision pipeline to
            # silently fail for all YouTube-sourced videos.
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(settings.UPLOAD_DIR, f'{video_id}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }

        # Run yt-dlp synchronously in a thread
        def _download(ydl_opts_custom):
            with YoutubeDL(ydl_opts_custom) as ydl:
                info = ydl.extract_info(url, download=False)
                
                duration = info.get("duration", 0)
                ydl.download([url])
                
                ext = info.get('ext', 'mp4')
                path = os.path.join(settings.UPLOAD_DIR, f"{video_id}.{ext}")
                return {
                    "title": info.get("title", "Unknown"),
                    "duration_seconds": duration,
                    "thumbnail": info.get("thumbnail"),
                    "channel_name": info.get("uploader"),
                    "path": path
                }
                
        try:
            # First attempt: normal download
            opts = dict(base_ydl_opts)
            return await asyncio.to_thread(_download, opts)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            # Second attempt: Chrome cookies (ISSUE-021)
            if os.path.exists("/.dockerenv"):
                raise Exception("youtube_bot_protection")
            try:
                opts = dict(base_ydl_opts)
                opts['cookiesfrombrowser'] = ('chrome',)
                return await asyncio.to_thread(_download, opts)
            except Exception:
                # If both fail, raise the protection error
                raise Exception("youtube_bot_protection")

youtube_service = YouTubeService()

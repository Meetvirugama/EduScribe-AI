import os
import asyncio
from yt_dlp import YoutubeDL
from fastapi import HTTPException
from services.transcript.url_normalizer import URLNormalizer
from core.config import settings


class YouTubeService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    def validate_url(self, url: str):
        URLNormalizer.validate_and_normalize(url)

    async def download_video(self, url: str, video_id: str) -> dict:
        self.validate_url(url)

        base_ydl_opts = {
            # Vision pipeline is disabled, so we only need audio for STT fallback.
            # Downloading audio-only is much faster and saves bandwidth.
            'noplaylist': True,
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
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
            # Second attempt: Chrome cookies
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

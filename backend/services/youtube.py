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
        if parsed.netloc not in ("www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com"):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    async def fetch_metadata(self, url: str) -> dict:
        self.validate_url(url)
        
        base_ydl_opts = {
            'quiet': True,
            'no_warnings': True,
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
        except Exception as e:
            # Fallback to cookies if metadata fetch is blocked
            opts = dict(base_ydl_opts)
            opts['cookiesfrombrowser'] = ('chrome',)
            return await asyncio.to_thread(_fetch, opts)

    async def download_video(self, url: str, video_id: str) -> dict:
        self.validate_url(url)
        
        base_ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(settings.UPLOAD_DIR, f'{video_id}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        # Run yt-dlp synchronously in a thread
        def _download(ydl_opts_custom):
            with YoutubeDL(ydl_opts_custom) as ydl:
                info = ydl.extract_info(url, download=False)
                
                duration = info.get("duration", 0)
                if duration > 4 * 3600:
                    raise ValueError("Video too long (max 4 hours)")
                    
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
        except Exception as first_error:
            # Second attempt: Chrome cookies
            try:
                opts = dict(base_ydl_opts)
                opts['cookiesfrombrowser'] = ('chrome',)
                return await asyncio.to_thread(_download, opts)
            except Exception as second_error:
                # If both fail, raise the protection error
                raise Exception("youtube_bot_protection")

    async def fetch_captions(self, video_url: str, video_id: str) -> dict:
        self.validate_url(video_url)
        # extract just the youtube ID from URL or assume video_id from db is the youtube ID? 
        # wait, the video_id from db is a UUID. We need the youtube ID!
        parsed = urlparse(video_url)
        # handle different youtube URL formats
        yt_id = None
        if "youtu.be" in parsed.netloc:
            yt_id = parsed.path.lstrip('/')
        else:
            from urllib.parse import parse_qs
            qs = parse_qs(parsed.query)
            if 'v' in qs:
                yt_id = qs['v'][0]
        
        if not yt_id:
            raise ValueError("Could not extract YouTube ID")

        from youtube_transcript_api import YouTubeTranscriptApi
        import json

        def _fetch():
            transcript_list = YouTubeTranscriptApi().list(yt_id)
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
            except:
                transcript = transcript_list.find_generated_transcript(['en'])
            
            transcript_data = transcript.fetch()
            
            simplified_segments = []
            full_text = []
            for item in transcript_data:
                # Handle both dicts (older versions) and objects (newer versions)
                start = item['start'] if isinstance(item, dict) else item.start
                text_raw = item['text'] if isinstance(item, dict) else item.text
                duration = item['duration'] if isinstance(item, dict) else item.duration
                
                text = text_raw.replace('\n', ' ').strip()
                simplified_segments.append({
                    "start": start,
                    "end": start + duration,
                    "text": text
                })
                full_text.append(text)
                
            os.makedirs(settings.TRANSCRIPT_DIR, exist_ok=True)
            transcript_json_path = os.path.join(settings.TRANSCRIPT_DIR, f"{video_id}.json")
            transcript_txt_path = os.path.join(settings.TRANSCRIPT_DIR, f"{video_id}.txt")
            
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(simplified_segments, f, indent=2, ensure_ascii=False)
                
            full_text_str = " ".join(full_text)
            with open(transcript_txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text_str)
                
            return {
                "json_path": transcript_json_path,
                "txt_path": transcript_txt_path,
                "language": transcript.language_code,
                "word_count": len(full_text_str.split())
            }

        return await asyncio.to_thread(_fetch)

youtube_service = YouTubeService()

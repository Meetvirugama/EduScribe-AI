import os
import asyncio
# pyrefly: ignore [missing-import]
import ffmpeg
from core.config import settings

class AudioService:
    def __init__(self):
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    async def extract_audio(self, video_path: str, video_id: str) -> str:
        if not os.path.exists(video_path):
            raise Exception("Video not found")
            
        audio_path = os.path.join(settings.TEMP_DIR, f"{video_id}.wav")

        def _process():
            # Probe metadata
            try:
                probe = ffmpeg.probe(video_path)
                format_info = probe.get('format', {})
                duration = float(format_info.get('duration', 0))
                size = int(format_info.get('size', 0))
                
                if duration > 4 * 3600:
                    raise Exception("Video exceeds 4 hour maximum duration")
                
                max_size_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
                if size > max_size_bytes:
                    raise Exception(f"Video exceeds {settings.MAX_VIDEO_SIZE_MB}MB size limit")
            except ffmpeg.Error as e:
                raise Exception(f"Failed to probe video: {e.stderr.decode('utf8', errors='ignore')}")
                
            try:
                (
                    ffmpeg
                    .input(video_path)
                    .output(audio_path, acodec='pcm_s16le', ac=1, ar='16k', af='loudnorm,afftdn')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                raise Exception(f"FFmpeg extraction failed: {e.stderr.decode('utf8', errors='ignore')}")

        await asyncio.to_thread(_process)
        return audio_path

audio_service = AudioService()

import os
import json
import asyncio
import whisper
from core.config import settings

class WhisperService:
    def __init__(self):
        os.makedirs(settings.TRANSCRIPT_DIR, exist_ok=True)
        # Load model lazily to save memory during startup
        self.model = None
        import threading
        self._model_lock = threading.Lock()

    def _get_model(self):
        if self.model is None:
            with self._model_lock:
                if self.model is None:
                    import logging
                    logging.getLogger(__name__).info("Loading Whisper model '%s'...", settings.WHISPER_MODEL)
                    self.model = whisper.load_model(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)
        return self.model

    async def transcribe(self, audio_path: str, video_id: str) -> dict:
        transcript_json_path = os.path.join(settings.TRANSCRIPT_DIR, f"{video_id}.json")
        transcript_txt_path = os.path.join(settings.TRANSCRIPT_DIR, f"{video_id}.txt")

        def _process():
            model = self._get_model()
            result = model.transcribe(audio_path, fp16=False)
            
            # Save JSON
            simplified_segments = []
            for segment in result.get('segments', []):
                simplified_segments.append({
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text", "").strip()
                })
            
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(simplified_segments, f, indent=2, ensure_ascii=False)
                
            # Save TXT
            with open(transcript_txt_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
                
            word_count = len(result['text'].split())
            return {
                "json_path": transcript_json_path,
                "txt_path": transcript_txt_path,
                "language": result.get("language", "unknown"),
                "word_count": word_count
            }

        return await asyncio.to_thread(_process)

whisper_service = WhisperService()

"""
Transcription service using faster-whisper (CTranslate2 backend).

faster-whisper is a reimplementation of OpenAI Whisper using CTranslate2,
providing 4–8x speed improvements on CPU vs openai-whisper, with INT8
quantization reducing memory usage by ~50%.

Key improvements over openai-whisper:
  - 4x faster on CPU (INT8 quantized inference)
  - Lower memory footprint (~75MB vs ~150MB for base model)
  - Streaming segment generation (lower latency to first output)
  - Model is unloaded after each transcription to free RAM for OCR
"""
import os
import json
import asyncio
import gc
import threading
import logging

from core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self):
        os.makedirs(settings.TRANSCRIPT_DIR, exist_ok=True)
        # Model is lazy-loaded on first transcription request.
        # Thread lock prevents concurrent load attempts from spawning duplicate
        # models.
        self.model = None
        self._model_lock = threading.Lock()

    def _get_model(self):
        """Lazy-load the faster-whisper model with double-checked locking."""
        if self.model is None:
            with self._model_lock:
                if self.model is None:
                    # pyrefly: ignore [missing-import]
                    from faster_whisper import WhisperModel
                    logger.info(
                        "Loading faster-whisper model '%s' on device='%s' with INT8 compute...",
                        settings.WHISPER_MODEL,
                        settings.WHISPER_DEVICE,
                    )
                    # compute_type="int8" quantizes the model weights to 8-bit integers,
                    # reducing VRAM/RAM usage by ~50% with minimal accuracy degradation.
                    # On CPU, INT8 is significantly faster than FP32.
                    self.model = WhisperModel(
                        settings.WHISPER_MODEL,
                        device=settings.WHISPER_DEVICE,
                        compute_type="int8",
                    )
        return self.model

    def _unload_model(self):
        """
        Explicitly unload the model to free RAM after transcription.

        Whisper models occupy 75MB–6GB depending on size. Releasing the model
        after each transcription frees memory for the subsequent OCR pipeline,
        which is also memory-intensive. The ~5s reload cost is acceptable for
        infrequent batch processing.
        """
        if self.model is not None:
            with self._model_lock:
                if self.model is not None:
                    logger.info(
                        "Unloading faster-whisper model to free RAM for OCR pipeline.")
                    del self.model
                    self.model = None
                    gc.collect()


    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def transcribe(self, audio_path: str, video_id: str, language: str = None) -> dict:
        """
        Transcribe an audio file to timestamped JSON and plain-text TXT.

        Uses faster-whisper's streaming segment generator, which begins
        producing segments without waiting for full audio to be processed.

        Args:
            audio_path: Absolute path to the WAV audio file.
            video_id:   UUID string for output file naming.
            language:   Optional language code (e.g. "en") to force transcription language.

        Returns:
            dict with keys: json_path, txt_path, language, word_count
        """
        transcript_json_path = os.path.join(
            settings.TRANSCRIPT_DIR, f"{video_id}.json")
        transcript_txt_path = os.path.join(
            settings.TRANSCRIPT_DIR, f"{video_id}.txt")

        def _process():
            model = self._get_model()

            # faster-whisper returns a generator of Segment namedtuples.
            # beam_size=5 is the default (same as openai-whisper).
            segments_generator, info = model.transcribe(
                audio_path,
                beam_size=5,
                language=language,  # Use provided language or auto-detect if None
                vad_filter=True,  # Voice Activity Detection: skip silence, ~20% faster
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            detected_language = info.language

            simplified_segments = []
            full_text_parts = []

            for segment in segments_generator:
                text = segment.text.strip()
                simplified_segments.append({
                    "start": round(segment.start, 3),
                    "end": round(segment.end, 3),
                    "text": text,
                    "avg_logprob": round(getattr(segment, "avg_logprob", 0.0), 3),
                    "no_speech_prob": round(getattr(segment, "no_speech_prob", 0.0), 3),
                })
                full_text_parts.append(text)

            full_text = " ".join(full_text_parts)

            # Save JSON (for API/downstream consumption)
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(simplified_segments, f, indent=2, ensure_ascii=False)

            # Save TXT (human-readable)
            with open(transcript_txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)

            word_count = len(full_text.split())

            return {
                "json_path": transcript_json_path,
                "txt_path": transcript_txt_path,
                "language": detected_language or "unknown",
                "word_count": word_count,
            }

        try:
            result = await asyncio.to_thread(_process)
        finally:
            # Always unload the model after transcription, whether it succeeded or not.
            # This ensures the OCR pipeline has maximum available RAM.
            self._unload_model()

        return result


whisper_service = WhisperService()

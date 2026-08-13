import os
import json
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Dict, Any
from core.config import settings


from tenacity import retry, stop_after_attempt, wait_exponential

class CaptionService:
    """
    Handles discovery and acquisition of captions using youtube-transcript-api.
    Preserves raw artifacts before parsing.
    """

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def discover_and_acquire(
            video_id: str, requested_language: str = "en") -> Dict[str, Any]:
        """
        Discovers the best transcript track, acquires it, and returns the raw payload.
        Throws exceptions if unavailable.
        """
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        selected_track = None
        source_type = "unknown"

        # 1. Try to find exact manual caption
        try:
            selected_track = transcript_list.find_manually_created_transcript([
                                                                              requested_language])
            source_type = "manual"
        except Exception:
            # 2. Try automatic caption
            try:
                selected_track = transcript_list.find_generated_transcript(
                    [requested_language])
                source_type = "automatic"
            except Exception:
                # 3. Fallback: Translation of an existing track
                try:
                    # Just grab any manual track and translate it
                    for manual_track in transcript_list._manually_created_transcripts.values():
                        if manual_track.is_translatable:
                            selected_track = manual_track.translate(
                                requested_language)
                            source_type = "translated"
                            break
                except Exception:
                    pass

        if not selected_track:
            raise Exception("NO_TRANSCRIPT_SOURCE")

        # Acquire
        try:
            fetched = selected_track.fetch()
            raw_data = fetched.to_raw_data() if hasattr(
                fetched, 'to_raw_data') else list(fetched)
        except Exception as e:
            raise Exception(f"CAPTION_ACQUISITION_FAILED: {str(e)}")

        if not raw_data:
            raise Exception("EMPTY_TRANSCRIPT")

        # Preserve Raw Artifact
        raw_dir = os.path.join(settings.UPLOAD_DIR, "raw_transcripts")
        os.makedirs(raw_dir, exist_ok=True)
        raw_path = os.path.join(raw_dir, f"{video_id}_raw.json")

        payload = {
            "video_id": video_id,
            "language": requested_language,
            "source_type": source_type,
            "raw_segments": raw_data
        }

        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return payload

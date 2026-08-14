import logging
import traceback
import os
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.utils import parse_video_id
from core.config import settings
from models.video import Video, VideoStatus, SourceType
from models.transcript import Transcript, TranscriptSource
from models.vision import VideoFrame, OCRResult, FrameScore

from services.youtube import youtube_service
from services.audio import audio_service, whisper_service
from services.vision.pipeline import vision_pipeline

from services.merge.builder import merge_builder, save_merged_lecture, render_merged_lecture_md
from services.content.pipeline import ContentPipeline
from services.llm.llm_manager import LLMManager

logger = logging.getLogger(__name__)


async def _set_video_error(video_id, error_message: str) -> None:
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Video).where(Video.id == video_id))
            video = res.scalar_one_or_none()
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = str(error_message)[:2000]
                await db.commit()
    except Exception as db_err:
        logger.error("Could not persist error state for video %s: %s", video_id, db_err)


async def process_video_pipeline_async(video_id_str: str):
    """
    Background orchestrator that runs the entire pipeline for a video.
    
    Refactored Pipeline steps:
      1. YouTube Download (if applicable)
      2. Audio Extraction (WAV)
      3. Whisper Transcription
      4. Vision Pipeline (frames + OCR + scoring)
      5. Merge Pipeline (Transcript + Vision -> MergedLecture JSON)
      6. Content Pipeline (MergedLecture -> LearningContext JSON)
      7. Complete (Artifacts generated on-demand later via /generate)
    """
    video_id = parse_video_id(video_id_str)

    async def update_status(db: AsyncSession, status: VideoStatus, current_step: str, progress: int):
        res = await db.execute(select(Video).where(Video.id == video_id))
        video = res.scalar_one_or_none()
        if video:
            video.status = status
            video.current_step = current_step
            video.progress_percent = progress
            await db.commit()

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()

            if not video:
                logger.error("Video %s not found in database. Aborting pipeline.", video_id_str)
                return

            video.processing_started_at = datetime.now(tz=timezone.utc)
            await db.commit()

            # ── STEP 1: YouTube Metadata Fetch ──────────────────────
            if video.source_type == SourceType.YOUTUBE:
                await update_status(db, VideoStatus.UPLOADING, "Fetching Metadata", 10)
                from services.transcript.metadata import MetadataAcquisition
                metadata = await MetadataAcquisition.fetch_metadata(video.youtube_url)
                video.title = metadata["title"]
                video.duration_seconds = metadata["duration_seconds"]
                video.thumbnail = metadata["thumbnail"]
                video.channel_name = metadata["channel_name"]
                await db.commit()

            # ── STEP 2 & 3: Transcript Acquisition ────────────────────────────
            # Try YouTube Captions first, fallback to Whisper STT
            transcript_fetched = False
            transcript_path = os.path.join(settings.TRANSCRIPT_DIR, f"{video_id_str}.json")
            os.makedirs(settings.TRANSCRIPT_DIR, exist_ok=True)
            
            if video.source_type == SourceType.YOUTUBE:
                await update_status(db, VideoStatus.TRANSCRIBING, "Fetching YouTube Captions", 20)
                try:
                    from services.transcript.captions import CaptionDiscovery
                    from services.transcript.canonicalizer import Canonicalizer
                    from services.transcript.exporter import Exporter
                    from services.transcript.models import DiscoveryStatus
                    from services.transcript.errors import CaptionDiscoveryError
                    
                    result = await CaptionDiscovery.discover_and_acquire(video_id_str)
                    if result.status == DiscoveryStatus.SUCCESS:
                        canonical_segments = Canonicalizer.canonicalize_youtube_captions(
                            result.segments,
                            language=result.actual_language or "en",
                            source_type=result.source_type
                        )
                        
                        # Convert TranscriptSegment dataclasses to dicts for exporter
                        canonical_dicts = [seg.to_dict() for seg in canonical_segments]

                        # Export artifacts
                        output_dir = os.path.join(settings.OUTPUT_DIR, video_id_str)
                        metadata = {"title": video.title, "duration_seconds": video.duration_seconds}
                        artifacts = Exporter.export_all(canonical_dicts, metadata, output_dir)
                        logger.info("Successfully exported transcript artifacts: %s", json.dumps(artifacts))
                        
                        word_count = sum(len(seg["text"].split()) for seg in canonical_dicts)
                        transcript = Transcript(
                            video_id=video_id,
                            transcript_path=os.path.join(output_dir, "transcript.json"),
                            language=result.actual_language or "en",
                            word_count=word_count,
                            source=TranscriptSource.YOUTUBE_CAPTIONS,
                        )
                        db.add(transcript)
                        await db.commit()
                        transcript_fetched = True
                        logger.info("Successfully fetched YouTube captions for %s", video_id_str)
                    else:
                        logger.warning("YouTube captions not found (Status: %s, Reason: %s)", result.status, result.reason)
                except Exception as e:
                    logger.warning("Failed to fetch YouTube captions for %s: %s. Falling back to Whisper STT.", video_id_str, e)
            
            if not transcript_fetched:
                if os.getenv("ENABLE_STT_FALLBACK", "false").lower() != "true":
                    raise Exception("YouTube captions were not found. Video download fallback is disabled by ENABLE_STT_FALLBACK.")
                
                logger.info("YouTube captions unavailable. Attempting Whisper STT fallback for video %s", video_id_str)
                if video.source_type == SourceType.YOUTUBE:
                    await update_status(db, VideoStatus.UPLOADING, "Downloading Audio Fallback", 25)
                    yt_info = await youtube_service.download_video(video.youtube_url, video_id_str)
                    video.video_path = yt_info["path"]
                    await db.commit()

                if not video.video_path or not os.path.exists(video.video_path):
                    raise Exception("Video/Audio file not found for fallback transcription.")

                # ── Fallback STEP 2: Extract Audio ─────────────────────────────────────────
                await update_status(db, VideoStatus.EXTRACTING_AUDIO, "Extracting Audio (WAV)", 20)
                audio_path = await audio_service.extract_audio(video.video_path, video_id_str)

                # ── Fallback STEP 3: Transcribe Audio ────────────────────────────
                await update_status(db, VideoStatus.TRANSCRIBING, "Transcribing Audio (faster-whisper)", 40)
                transcript_res = await whisper_service.transcribe(audio_path, video_id_str)

                # Export Whisper result
                try:
                    from services.transcript.canonicalizer import Canonicalizer
                    from services.transcript.exporter import Exporter
                    with open(transcript_res["json_path"], "r", encoding="utf-8") as f:
                        whisper_data = json.load(f)
                    if "segments" in whisper_data:
                        raw_whisper = whisper_data["segments"]
                        canonical_segments = Canonicalizer.canonicalize_whisper_stt(raw_whisper, transcript_res["language"])
                        
                        canonical_dicts = [seg.to_dict() for seg in canonical_segments]
                        
                        output_dir = os.path.join(settings.OUTPUT_DIR, video_id_str)
                        metadata = {"title": video.title, "duration_seconds": video.duration_seconds}
                        artifacts = Exporter.export_all(canonical_dicts, metadata, output_dir)
                        logger.info("Successfully exported fallback Whisper artifacts: %s", json.dumps(artifacts))
                        transcript_res["json_path"] = os.path.join(output_dir, "transcript.json")
                except Exception as e:
                    logger.warning("Failed to export Whisper transcripts to canonical formats: %s", e)

                transcript = Transcript(
                    video_id=video_id,
                    transcript_path=transcript_res["json_path"],
                    language=transcript_res["language"],
                    word_count=transcript_res["word_count"],
                    source=TranscriptSource.WHISPER_AUDIO,
                )
                db.add(transcript)
                await db.commit()

                if os.path.exists(audio_path):
                    os.remove(audio_path)

            # ── STEP 4: Vision Pipeline (Disabled) ────────────────────────────
            # await update_status(db, VideoStatus.EXTRACTING_FRAMES, "Running Vision Pipeline", 60)
            # vision_stats = await vision_pipeline.run(video_id_str, video.video_path)
            # logger.info("Vision Pipeline Stats: %s", vision_stats)

            # ── STEP 5: Merge Pipeline ──────────────
            await update_status(db, VideoStatus.CHUNKING, "Aligning transcript", 70)

            try:
                with open(transcript.transcript_path, "r", encoding="utf-8") as f:
                    transcript_data = json.load(f)
                if isinstance(transcript_data, dict) and "segments" in transcript_data:
                    transcript_segments = transcript_data["segments"]
                else:
                    transcript_segments = transcript_data
            except Exception as e:
                logger.error("Failed to read transcript for video %s: %s", video_id_str, e)
                transcript_segments = []

            # Vision pipeline disabled; no frames
            frames_data = []

            # Build and save MergedLecture (Source of Truth)
            merged_lecture = merge_builder.build(
                video_id=video_id_str,
                transcript_segments=transcript_segments,
                frames_data=frames_data,
                metadata={"title": video.title, "duration": video.duration_seconds}
            )
            
            output_dir = os.path.join(settings.OUTPUT_DIR, video_id_str)
            save_merged_lecture(merged_lecture, output_dir)
            
            # Optional: generate MD for debugging (not used by system)
            if os.getenv("DEBUG_MODE") == "true":
                render_merged_lecture_md(merged_lecture, output_dir)

            # ── STEP 6: Content Pipeline (Knowledge Extraction) ──────────────────────────
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Extracting Knowledge", 80)
            
            llm_manager = LLMManager()
            content_pipeline = ContentPipeline(llm_manager)
            learning_context = await content_pipeline.build_learning_context(merged_lecture, output_dir=output_dir)

            # Save LearningContext to disk
            learning_context_path = os.path.join(output_dir, "learning_context.json")
            with open(learning_context_path, "w", encoding="utf-8") as f:
                # Store the state dict containing all extracted data
                import dataclasses
                # Convert Pydantic models to dicts for JSON serialization
                def pydantic_encoder(obj):
                    if hasattr(obj, "model_dump"):
                        return obj.model_dump()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                json.dump(dataclasses.asdict(learning_context.state), f, indent=2, default=pydantic_encoder)

            # ── STEP 7: Complete ──────────────────────────────────────────────
            processing_time = None
            if video.processing_started_at:
                elapsed = datetime.now(tz=timezone.utc) - video.processing_started_at.replace(tzinfo=timezone.utc)
                processing_time = int(elapsed.total_seconds())

            res = await db.execute(select(Video).where(Video.id == video_id))
            video = res.scalar_one_or_none()
            if video:
                video.status = VideoStatus.READY_FOR_SELECTION
                video.current_step = "Ready for Selection"
                video.progress_percent = 100
                if processing_time is not None:
                    video.processing_time_seconds = processing_time
                await db.commit()

            logger.info("Pipeline completed for video %s in %ss", video_id_str, processing_time or "N/A")

    except Exception as e:
        logger.error("Pipeline failed for video %s: %s\n%s", video_id_str, str(e), traceback.format_exc())
        await _set_video_error(video_id, str(e))

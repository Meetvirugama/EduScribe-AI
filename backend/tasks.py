"""
Background task pipeline for EduScribe AI video processing.

Orchestrates:
    1. YouTube metadata fetch / download
    2. Audio extraction (FFmpeg)
    3. Whisper transcription
    4. (For uploaded videos) Frame extraction pipeline

All heavy work runs via asyncio.to_thread inside FastAPI BackgroundTasks.
"""
import logging
import os
import time
import uuid
from typing import Optional

from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.video import Video, VideoStatus, SourceType
from models.transcript import Transcript
from services import youtube_service, audio_service, whisper_service
from services.vision.pipeline import vision_pipeline, VisionPipelineError

logger = logging.getLogger(__name__)


async def process_video_pipeline_async(video_id: str) -> None:  # noqa: C901 (complexity OK for orchestrator)
    """
    Main video processing pipeline.

    Runs as a FastAPI BackgroundTask after a video record is created.
    Updates `videos.status`, `videos.progress_percent`, and
    `videos.current_step` throughout for live UI feedback.

    Args:
        video_id: UUID string of the video to process.
    """
    start_time = time.time()
    audio_path: Optional[str] = None

    async def update_progress(percent: int, step: str, eta: Optional[int] = None) -> None:
        """Write live progress back to the DB without re-using the outer session."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).where(Video.id == uuid.UUID(video_id)))
            v = result.scalar_one_or_none()
            if v:
                v.progress_percent = percent
                v.current_step = step
                if eta is not None:
                    v.estimated_time_remaining_seconds = eta
                await db.commit()

    async with AsyncSessionLocal() as db:
        try:
            # ---------------------------------------------------------------- #
            # Load video record
            # ---------------------------------------------------------------- #
            result = await db.execute(select(Video).where(Video.id == uuid.UUID(video_id)))
            video = result.scalar_one_or_none()
            if not video:
                logger.error("Pipeline called for unknown video_id: %s", video_id)
                return

            # ---------------------------------------------------------------- #
            # YouTube path
            # ---------------------------------------------------------------- #
            if video.source_type == SourceType.YOUTUBE:
                video.status = VideoStatus.PROCESSING
                await db.commit()

                await update_progress(10, "Fetching Video Metadata...", 5)
                meta_info = await youtube_service.fetch_metadata(video.youtube_url)
                video.title = meta_info["title"]
                video.duration_seconds = meta_info["duration_seconds"]
                video.thumbnail = meta_info["thumbnail"]
                video.channel_name = meta_info["channel_name"]
                await db.commit()

                await update_progress(30, "Downloading Captions...", 3)
                trans_info = None
                transcript_source = "whisper_audio"

                try:
                    trans_info = await youtube_service.fetch_captions(video.youtube_url, video_id)
                    transcript_source = "youtube_captions"
                    logger.info("YouTube captions fetched for video %s", video_id)
                except Exception as cap_err:
                    logger.info(
                        "No captions for video %s; falling back to Whisper: %s", video_id, cap_err
                    )

                if not trans_info:
                    eta = int((video.duration_seconds or 300) * 0.1)
                    await update_progress(40, "Downloading Audio Stream...", eta)
                    dl_info = await youtube_service.download_video(video.youtube_url, video_id)
                    video.video_path = dl_info["path"]
                    await db.commit()

                    await update_progress(50, "Extracting Audio Track...", eta)
                    audio_path = await audio_service.extract_audio(video.video_path, video_id)

                    video.status = VideoStatus.TRANSCRIBING
                    await db.commit()

                    eta_tr = int((video.duration_seconds or 300) * 0.4)
                    await update_progress(60, "Transcribing with Whisper AI...", eta_tr)
                    trans_info = await whisper_service.transcribe(audio_path, video_id)

            # ---------------------------------------------------------------- #
            # Uploaded video path
            # ---------------------------------------------------------------- #
            else:
                video.status = VideoStatus.PROCESSING
                await db.commit()

                # --- Frame extraction (non-blocking; errors are logged, not fatal) ---
                if video.video_path:
                    await update_progress(20, "Detecting Scenes...", 15)
                    try:
                        pipeline_result = await vision_pipeline.run(
                            video_id=video_id,
                            video_path=video.video_path,
                        )
                        logger.info(
                            "Frame pipeline result for video %s: %s", video_id, pipeline_result
                        )
                    except VisionPipelineError as vpe:
                        logger.warning(
                            "Frame pipeline failed (non-fatal) for video %s: %s", video_id, vpe
                        )
                    except Exception as exc:
                        logger.warning(
                            "Unexpected frame pipeline error for video %s: %s", video_id, exc
                        )

                await update_progress(50, "Extracting Audio Track...", 10)
                audio_path = await audio_service.extract_audio(video.video_path, video_id)

                video.status = VideoStatus.TRANSCRIBING
                await db.commit()

                await update_progress(65, "Transcribing with Whisper AI...", 120)
                trans_info = await whisper_service.transcribe(audio_path, video_id)
                transcript_source = "manual_upload"

            # ---------------------------------------------------------------- #
            # Persist transcript record
            # ---------------------------------------------------------------- #
            await update_progress(90, "Finalizing Database Records...", 2)
            transcript = Transcript(
                video_id=video.id,
                transcript_path=trans_info["json_path"],
                language=trans_info["language"],
                word_count=trans_info["word_count"],
                source=transcript_source,
            )
            db.add(transcript)

            processing_time = int(time.time() - start_time)
            video.status = VideoStatus.COMPLETED
            video.progress_percent = 100
            video.current_step = "Completed"
            video.processing_time_seconds = processing_time
            video.estimated_time_remaining_seconds = 0
            await db.commit()

            logger.info("Pipeline completed for video %s in %ds", video_id, processing_time)

        except Exception as exc:
            logger.exception("Pipeline failed for video %s: %s", video_id, exc)
            try:
                result = await db.execute(select(Video).where(Video.id == uuid.UUID(video_id)))
                video = result.scalar_one_or_none()
                if video:
                    video.status = VideoStatus.FAILED
                    video.error_message = str(exc)
                    await db.commit()
            except Exception as db_err:
                logger.error(
                    "Could not update FAILED status for video %s: %s", video_id, db_err
                )

        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.info("Cleaned up temporary audio file: %s", audio_path)
                except OSError as cleanup_err:
                    logger.warning(
                        "Failed to clean up audio file %s: %s", audio_path, cleanup_err
                    )

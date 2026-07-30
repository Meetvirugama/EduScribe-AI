"""
Vision pipeline orchestrator.

Coordinates the full frame extraction pipeline:
    1. Scene Detection
    2. Frame Extraction (sharpest mid-scene frame)
    3. Blur Filtering
    4. Duplicate Removal
    5. OCR Text Extraction
    6. Transcript Matching
    7. Frame Scoring & Selection
    8. Database Persistence

This module is intentionally stateless and re-entrant so it can be
invoked from FastAPI BackgroundTasks or a Celery worker.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.vision import VideoFrame, FrameMetadata, OCRResult, FrameScore
from models.transcript import Transcript
from services.vision.scene_detector import scene_detector_service, SceneDetectionError
from services.vision.frame_extractor import frame_extractor_service, FrameExtractionError
from services.vision.blur_detector import filter_blurry_frames
from services.vision.duplicate_detector import deduplicate_frames
from services.vision.ocr_service import ocr_service, OCRServiceError
from services.vision.transcript_matcher import transcript_matcher_service
from services.vision.frame_scorer import rank_and_select_frames

logger = logging.getLogger(__name__)


class VisionPipelineError(Exception):
    """Top-level error for the vision pipeline."""


class VisionPipeline:
    """
    Orchestrates the end-to-end frame intelligence pipeline.

    Usage:
        pipeline = VisionPipeline()
        result = await pipeline.run(video_id="...", video_path="...")
    """

    async def run(
        self,
        video_id: str,
        video_path: str,
        top_frames_per_group: int = 1,
    ) -> Dict[str, Any]:
        """
        Execute the full vision pipeline for a video.

        Args:
            video_id:             UUID string of the video record.
            video_path:           Absolute path to the video file.
            top_frames_per_group: How many top frames to mark as selected.

        Returns:
            Summary dict with counts of detected/selected/discarded frames.

        Raises:
            VisionPipelineError: If a non-recoverable error occurs.
        """
        logger.info("VisionPipeline.run() started for video %s", video_id)

        # ------------------------------------------------------------------ #
        # 1. Load existing transcript path from DB
        # ------------------------------------------------------------------ #
        transcript_path: Optional[str] = await self._get_transcript_path(video_id)
        if not transcript_path:
            logger.warning(
                "No transcript found for video %s – OCR matching will score 0.", video_id
            )

        # ------------------------------------------------------------------ #
        # 2. Scene detection
        # ------------------------------------------------------------------ #
        try:
            scenes = await scene_detector_service.detect_scenes(video_path)
        except SceneDetectionError as exc:
            raise VisionPipelineError(f"Scene detection failed: {exc}") from exc

        if not scenes:
            logger.warning("No scenes detected for video %s – aborting pipeline.", video_id)
            return {"scenes": 0, "frames_extracted": 0, "frames_selected": 0}

        # ------------------------------------------------------------------ #
        # 3. Frame extraction
        # ------------------------------------------------------------------ #
        try:
            raw_frames = await frame_extractor_service.extract_best_frames(
                video_path, video_id, scenes
            )
        except FrameExtractionError as exc:
            raise VisionPipelineError(f"Frame extraction failed: {exc}") from exc

        if not raw_frames:
            logger.warning("No frames extracted for video %s.", video_id)
            return {"scenes": len(scenes), "frames_extracted": 0, "frames_selected": 0}

        # ------------------------------------------------------------------ #
        # 4. Blur filtering
        # ------------------------------------------------------------------ #
        sharp_frames, blurry_frames = filter_blurry_frames(raw_frames)
        logger.info(
            "Blur filter: %d sharp / %d blurry (video=%s)",
            len(sharp_frames), len(blurry_frames), video_id,
        )

        if not sharp_frames:
            logger.warning("All frames were blurry for video %s – using raw frames.", video_id)
            sharp_frames = raw_frames  # graceful degradation

        # ------------------------------------------------------------------ #
        # 5. Duplicate removal
        # ------------------------------------------------------------------ #
        unique_frames, dup_frames = deduplicate_frames(sharp_frames)
        logger.info(
            "Dedup: %d unique / %d duplicates (video=%s)",
            len(unique_frames), len(dup_frames), video_id,
        )

        if not unique_frames:
            unique_frames = sharp_frames  # graceful degradation

        # ------------------------------------------------------------------ #
        # 6. OCR
        # ------------------------------------------------------------------ #
        frames_with_ocr = await self._run_ocr_batch(unique_frames)

        # ------------------------------------------------------------------ #
        # 7. Transcript matching
        # ------------------------------------------------------------------ #
        if transcript_path:
            frames_with_ocr = transcript_matcher_service.match_frames_to_transcript(
                frames_with_ocr, transcript_path
            )

        # ------------------------------------------------------------------ #
        # 8. Scoring & selection
        # ------------------------------------------------------------------ #
        scored_frames = rank_and_select_frames(frames_with_ocr, top_n=top_frames_per_group)

        # ------------------------------------------------------------------ #
        # 9. Persist to database
        # ------------------------------------------------------------------ #
        await self._persist(video_id, scored_frames)

        selected_count = sum(1 for f in scored_frames if f.get("is_selected"))
        logger.info(
            "VisionPipeline complete for video %s: %d scenes, %d frames extracted, "
            "%d selected",
            video_id, len(scenes), len(scored_frames), selected_count,
        )

        return {
            "scenes": len(scenes),
            "frames_extracted": len(raw_frames),
            "frames_after_blur_filter": len(sharp_frames),
            "frames_after_dedup": len(unique_frames),
            "frames_selected": selected_count,
        }

    async def _get_transcript_path(self, video_id: str) -> Optional[str]:
        """Fetch the transcript JSON file path from the database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Transcript).where(Transcript.video_id == uuid.UUID(video_id))
            )
            transcript = result.scalar_one_or_none()
            if transcript and transcript.transcript_path:
                return transcript.transcript_path
        return None

    async def _run_ocr_batch(self, frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run OCR sequentially on each frame, tolerating per-frame failures."""
        enriched: List[Dict[str, Any]] = []
        for frame in frames:
            path = frame.get("frame_path", "")
            try:
                ocr_data = await ocr_service.extract_text(path)
                enriched.append(
                    {
                        **frame,
                        "raw_text": ocr_data["raw_text"],
                        "clean_text": ocr_data["clean_text"],
                        "average_confidence": ocr_data["average_confidence"],
                    }
                )
            except (FileNotFoundError, OCRServiceError) as exc:
                logger.warning("OCR skipped for frame %s: %s", path, exc)
                enriched.append(
                    {**frame, "raw_text": "", "clean_text": "", "average_confidence": 0.0}
                )
        return enriched

    async def _persist(self, video_id: str, scored_frames: List[Dict[str, Any]]) -> None:
        """
        Persist all frame metadata to the database in a single transaction.
        Deletes existing records for the video before inserting new ones
        to make the operation idempotent (safe to re-run).
        """
        async with AsyncSessionLocal() as db:
            # Idempotent: remove any previously extracted frames for this video
            existing = await db.execute(
                select(VideoFrame).where(VideoFrame.video_id == uuid.UUID(video_id))
            )
            for old_frame in existing.scalars().all():
                await db.delete(old_frame)
            await db.flush()

            for frame_data in scored_frames:
                frame_uuid = uuid.uuid4()

                db_frame = VideoFrame(
                    id=frame_uuid,
                    video_id=uuid.UUID(video_id),
                    timestamp_ms=frame_data.get("timestamp_ms", 0),
                    frame_path=frame_data.get("frame_path", ""),
                    scene_number=frame_data.get("scene_number", 0),
                )
                db.add(db_frame)
                await db.flush()

                db_meta = FrameMetadata(
                    frame_id=frame_uuid,
                    blur_score=frame_data.get("blur_score"),
                    phash=frame_data.get("phash"),
                    duration_ms=frame_data.get("duration_ms"),
                )
                db.add(db_meta)

                db_ocr = OCRResult(
                    frame_id=frame_uuid,
                    raw_text=frame_data.get("raw_text") or None,
                    clean_text=frame_data.get("clean_text") or None,
                    average_confidence=frame_data.get("average_confidence"),
                )
                db.add(db_ocr)

                db_score = FrameScore(
                    frame_id=frame_uuid,
                    transcript_similarity=frame_data.get("transcript_similarity"),
                    visual_importance_score=frame_data.get("visual_importance_score"),
                    is_selected=bool(frame_data.get("is_selected", False)),
                )
                db.add(db_score)

            await db.commit()
            logger.info("Persisted %d frames for video %s", len(scored_frames), video_id)

    async def delete_frames(self, video_id: str) -> int:
        """
        Delete all frame records and files for a given video.

        Returns:
            Number of VideoFrame records deleted.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(VideoFrame).where(VideoFrame.video_id == uuid.UUID(video_id))
            )
            frames = result.scalars().all()
            count = len(frames)
            for frame in frames:
                await db.delete(frame)
            await db.commit()

        # Delete files from disk
        await frame_extractor_service.delete_frames_for_video(video_id)
        logger.info("Deleted %d frame records for video %s", count, video_id)
        return count


vision_pipeline = VisionPipeline()

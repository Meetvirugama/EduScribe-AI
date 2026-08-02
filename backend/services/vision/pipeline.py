"""
Vision pipeline orchestrator.

Coordinates the full frame extraction pipeline:
    1. Scene Detection
    2. Frame Extraction (sharpest mid-scene frame)
    3. Duplicate Removal
    4. Blur Filtering
    5. OCR Text Extraction
    6. Transcript Matching
    7. Frame Scoring & Selection
    8. Database Persistence
    9. Temporary File Cleanup

This module is completely optimized for production long-video processing,
implementing state checkpoints, bulk database saving, and exact phase ordering.
"""
import logging
import uuid
import os
from dataclasses import dataclass, field
from core.utils import parse_video_id
from typing import List, Dict, Any, Optional

from sqlalchemy import select, delete

from core.database import AsyncSessionLocal
from models.vision import VideoFrame, FrameMetadata, OCRResult, FrameScore
from models.transcript import Transcript
from services.vision.scene.detector import scene_detector_service, SceneDetectionError
from services.vision.extraction.frame_extractor import frame_extractor_service, FrameExtractionError
from services.vision.filtering.blur_detector import filter_blurry_frames
from services.vision.filtering.duplicate_detector import deduplicate_frames
from services.vision.ocr.service import ocr_service, OCRServiceError
from services.vision.transcript.matcher import transcript_matcher_service
from services.vision.scoring.ranking_service import rank_and_trim_frames

logger = logging.getLogger(__name__)

# Pipeline configurations for optimizations
PIPELINE_CONFIG = {
    "enable_scene_cache": True,
    "enable_frame_cache": True,
    "enable_ocr_cache": True,
    "delete_unused_frames": True,
    "ocr_mode": "sequential",
    "max_frames_per_scene": 5
}

class VisionPipelineError(Exception):
    """Top-level error for the vision pipeline."""

@dataclass
class ProcessingContext:
    """
    Tracks the execution state of the video to allow resumability
    and graceful degradation upon stage failures.
    """
    video_id: str
    current_stage: str = "init"
    scene_count: int = 0
    frames_extracted: int = 0
    errors: List[str] = field(default_factory=list)
    
    # Checkpoints
    scene_completed: bool = False
    frames_completed: bool = False
    ocr_completed: bool = False
    ranking_completed: bool = False


class VisionPipeline:
    """
    Orchestrates the end-to-end frame intelligence pipeline.
    """

    async def run(
        self,
        video_id: str,
        video_path: str,
        top_frames_per_group: int = 1,
    ) -> Dict[str, Any]:
        """
        Execute the full vision pipeline for a video.
        """
        ctx = ProcessingContext(video_id=video_id)
        logger.info("VisionPipeline.run() started for video %s", video_id)

        # ------------------------------------------------------------------ #
        # 1. Transcript path
        # ------------------------------------------------------------------ #
        transcript_path: Optional[str] = await self._get_transcript_path(video_id)
        if not transcript_path:
            logger.warning("No transcript found for %s – OCR matching will score 0.", video_id)

        # ------------------------------------------------------------------ #
        # 2. Scene detection
        # ------------------------------------------------------------------ #
        ctx.current_stage = "scene_detection"
        try:
            scenes = await scene_detector_service.detect_scenes(video_path, video_id)
            ctx.scene_completed = True
            ctx.scene_count = len(scenes)
        except SceneDetectionError as exc:
            ctx.errors.append(str(exc))
            raise VisionPipelineError(f"Scene detection failed: {exc}") from exc

        if not scenes:
            return self._abort_early(ctx)

        # ------------------------------------------------------------------ #
        # 3. Frame extraction
        # ------------------------------------------------------------------ #
        ctx.current_stage = "frame_extraction"
        try:
            raw_frames = await frame_extractor_service.extract_best_frames(
                video_path, video_id, scenes
            )
            ctx.frames_completed = True
            ctx.frames_extracted = len(raw_frames)
        except FrameExtractionError as exc:
            ctx.errors.append(str(exc))
            raise VisionPipelineError(f"Frame extraction failed: {exc}") from exc

        if not raw_frames:
            return self._abort_early(ctx)

        # ------------------------------------------------------------------ #
        # 4. Duplicate removal (Runs first to minimize Blur CPU cost)
        # ------------------------------------------------------------------ #
        # Duplicate removal is performed before expensive analysis.
        # Removing visually identical frames reduces CPU usage in
        # later blur, OCR, and ranking stages.
        ctx.current_stage = "duplicate_removal"
        unique_frames, dup_frames = deduplicate_frames(raw_frames)
        logger.info(
            "Dedup: %d unique / %d duplicates (video=%s)",
            len(unique_frames), len(dup_frames), video_id,
        )
        if not unique_frames:
            unique_frames = raw_frames  # graceful degradation

        # ------------------------------------------------------------------ #
        # 5. Blur filtering
        # ------------------------------------------------------------------ #
        ctx.current_stage = "blur_filtering"
        sharp_frames, blurry_frames = filter_blurry_frames(unique_frames)
        logger.info(
            "Blur filter: %d sharp / %d blurry (video=%s)",
            len(sharp_frames), len(blurry_frames), video_id,
        )
        if not sharp_frames:
            sharp_frames = unique_frames  # graceful degradation

        # ------------------------------------------------------------------ #
        # 6. OCR
        # ------------------------------------------------------------------ #
        # OCR is executed sequentially by default because multiple
        # concurrent GPU inference calls can increase VRAM usage
        # and create unstable memory spikes.
        ctx.current_stage = "ocr"
        frames_with_ocr = await self._run_ocr_batch(sharp_frames)
        ctx.ocr_completed = True

        # ------------------------------------------------------------------ #
        # 7. Transcript matching
        # ------------------------------------------------------------------ #
        ctx.current_stage = "transcript_matching"
        if transcript_path:
            frames_with_ocr = transcript_matcher_service.match_frames_to_transcript(
                frames_with_ocr, transcript_path, video_id
            )

        # ------------------------------------------------------------------ #
        # 8. Scoring & selection
        # ------------------------------------------------------------------ #
        ctx.current_stage = "ranking"
        scored_frames = rank_and_trim_frames(frames_with_ocr, top_n=top_frames_per_group)
        ctx.ranking_completed = True

        # ------------------------------------------------------------------ #
        # 9. Persist to database & File cleanup
        # ------------------------------------------------------------------ #
        ctx.current_stage = "persistence"
        await self._persist_bulk(video_id, scored_frames)
        
        if PIPELINE_CONFIG["delete_unused_frames"]:
            self._cleanup_unused_frames(scored_frames, raw_frames)

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
            "errors": ctx.errors
        }

    def _abort_early(self, ctx: ProcessingContext) -> Dict[str, Any]:
        logger.warning("Pipeline aborting early at stage: %s for video %s", ctx.current_stage, ctx.video_id)
        return {
            "scenes": ctx.scene_count,
            "frames_extracted": ctx.frames_extracted,
            "frames_selected": 0,
            "errors": ctx.errors
        }

    async def _get_transcript_path(self, video_id: str) -> Optional[str]:
        """Fetch the transcript JSON file path from the database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Transcript).where(Transcript.video_id == parse_video_id(video_id))
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
                enriched.append({**frame, **ocr_data})
            except (FileNotFoundError, OCRServiceError) as exc:
                logger.warning("OCR skipped for frame %s: %s", path, exc)
                from services.vision.ocr.features import generate_ocr_features
                empty_data = {
                    "raw_text": "",
                    "clean_text": "",
                    **generate_ocr_features("", 0.0, 0)
                }
                enriched.append({**frame, **empty_data})
        return enriched

    async def _persist_bulk(self, video_id: str, scored_frames: List[Dict[str, Any]]) -> None:
        """
        Database writes use bulk operations because inserting
        thousands of frames individually creates unnecessary
        database round trips.
        """
        async with AsyncSessionLocal() as db:
            # Idempotent: remove any previously extracted frames for this video
            await db.execute(
                delete(VideoFrame).where(VideoFrame.video_id == parse_video_id(video_id))
            )
            await db.flush()

            db_frames = []
            db_metas = []
            db_ocrs = []
            db_scores = []

            for frame_data in scored_frames:
                frame_uuid = uuid.uuid4()
                
                db_frames.append(VideoFrame(
                    id=frame_uuid,
                    video_id=parse_video_id(video_id),
                    timestamp_ms=frame_data.get("timestamp_ms", 0),
                    frame_path=frame_data.get("frame_path", ""),
                    scene_number=frame_data.get("scene_number", 0),
                ))

                db_metas.append(FrameMetadata(
                    frame_id=frame_uuid,
                    blur_score=frame_data.get("blur_score"),
                    phash=frame_data.get("phash"),
                    duration_ms=frame_data.get("duration_ms"),
                ))

                db_ocrs.append(OCRResult(
                    frame_id=frame_uuid,
                    raw_text=frame_data.get("raw_text") or None,
                    clean_text=frame_data.get("clean_text") or None,
                    average_confidence=frame_data.get("average_confidence"),
                ))

                db_scores.append(FrameScore(
                    frame_id=frame_uuid,
                    transcript_similarity=frame_data.get("transcript_similarity"),
                    visual_importance_score=frame_data.get("visual_importance_score"),
                    is_selected=bool(frame_data.get("is_selected", False)),
                ))

            db.add_all(db_frames)
            await db.flush() # flush frames to get them into the session
            
            db.add_all(db_metas)
            db.add_all(db_ocrs)
            db.add_all(db_scores)

            await db.commit()
            logger.info("Bulk persisted %d frames for video %s", len(scored_frames), video_id)
            
    def _cleanup_unused_frames(self, selected_frames: List[Dict[str, Any]], all_frames: List[Dict[str, Any]]):
        """
        Deletes the physical files for frames that did not pass the selection criteria.
        Long videos create many temporary images which fill up disk space quickly.
        """
        selected_paths = {f.get("frame_path") for f in selected_frames if f.get("is_selected")}
        all_paths = {f.get("frame_path") for f in all_frames}
        
        unselected_paths = all_paths - selected_paths
        deleted = 0
        for path in unselected_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    deleted += 1
                except Exception as e:
                    logger.debug("Failed to delete unused frame %s: %s", path, e)
                    
        logger.info("Cleaned up %d unused frame files.", deleted)


    async def delete_frames(self, video_id: str) -> int:
        """
        Delete all frame records and files for a given video.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(VideoFrame).where(VideoFrame.video_id == parse_video_id(video_id))
            )
            count = result.rowcount
            await db.commit()

        # Delete files from disk
        await frame_extractor_service.delete_frames_for_video(video_id)
        logger.info("Deleted %d frame records for video %s", count, video_id)
        return count


vision_pipeline = VisionPipeline()

"""
Production-ready frame extraction service using OpenCV.
Extracts the sharpest frame from the middle third of each detected scene.
"""
import logging
import os
import asyncio
from typing import List, Dict, Any, Optional

import cv2

from core.config import settings

logger = logging.getLogger(__name__)


class FrameExtractionError(Exception):
    """Raised when frame extraction fails."""


class FrameExtractorService:
    """
    Extracts representative frames from video scenes.

    Strategy:
        For each scene, the middle-third window is sampled and the sharpest frame
        (highest Laplacian variance) is selected. This avoids blurry transition
        frames at scene boundaries and animation frames at scene starts.
    """

    def __init__(self) -> None:
        self._frames_dir: str = settings.FRAMES_DIR
        os.makedirs(self._frames_dir, exist_ok=True)

    def get_video_frames_dir(self, video_id: str) -> str:
        """Return the per-video frames directory, creating it if necessary."""
        path = os.path.join(self._frames_dir, video_id)
        os.makedirs(path, exist_ok=True)
        return path

    async def extract_best_frames(
        self,
        video_path: str,
        video_id: str,
        scenes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract the best (sharpest mid-scene) frame for each scene.

        Args:
            video_path: Absolute path to the video file.
            video_id:   UUID string of the video record.
            scenes:     List of scene dicts produced by SceneDetectorService.

        Returns:
            List of frame dicts with keys:
                - scene_number (int)
                - timestamp_ms (int)
                - frame_path (str)
                - duration_ms (int)

        Raises:
            FileNotFoundError: If the video file does not exist.
            FrameExtractionError: If extraction fails fatally.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not scenes:
            logger.warning("No scenes provided for video %s – skipping extraction.", video_id)
            return []

        output_dir = self.get_video_frames_dir(video_id)
        logger.info("Extracting frames for video %s into %s", video_id, output_dir)

        try:
            frames = await asyncio.to_thread(
                self._extract_frames_sync, video_path, video_id, scenes, output_dir
            )
        except Exception as exc:
            logger.error("Frame extraction failed for video %s: %s", video_id, exc)
            raise FrameExtractionError(f"Frame extraction failed: {exc}") from exc

        logger.info("Extracted %d frames for video %s", len(frames), video_id)
        return frames

    def _extract_frames_sync(
        self,
        video_path: str,
        video_id: str,
        scenes: List[Dict[str, Any]],
        output_dir: str,
    ) -> List[Dict[str, Any]]:
        """Synchronous frame extraction – runs inside asyncio.to_thread."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FrameExtractionError(f"OpenCV could not open video: {video_path}")

        extracted: List[Dict[str, Any]] = []

        try:
            for scene in scenes:
                frame_info = self._extract_best_from_scene(cap, scene, output_dir)
                if frame_info:
                    extracted.append(frame_info)
        finally:
            cap.release()

        return extracted

    def _extract_best_from_scene(
        self,
        cap: cv2.VideoCapture,
        scene: Dict[str, Any],
        output_dir: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Sample frames in the middle third of a scene and return the sharpest one.
        Returns None if no frame could be read.
        """
        scene_num = scene["scene_number"]
        start_ms = scene["start_time_ms"]
        end_ms = scene["end_time_ms"]
        duration_ms = end_ms - start_ms

        # Sample the middle third to avoid transition blur
        sample_start = start_ms + duration_ms // 3
        sample_end = end_ms - duration_ms // 3

        # If scene is too short, fall back to the exact midpoint
        if sample_start >= sample_end:
            sample_positions = [start_ms + duration_ms // 2]
        else:
            # Sample up to 5 evenly spaced positions within the middle third
            step = max(1, (sample_end - sample_start) // 5)
            sample_positions = list(range(sample_start, sample_end, step))[:5]

        best_frame = None
        best_score = -1.0
        best_ts_ms = sample_positions[0]

        for pos_ms in sample_positions:
            cap.set(cv2.CAP_PROP_POS_MSEC, pos_ms)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            score = self._laplacian_variance(frame)
            if score > best_score:
                best_score = score
                best_frame = frame
                best_ts_ms = pos_ms

        if best_frame is None:
            logger.warning("Could not read any frame from scene %d", scene_num)
            return None

        filename = f"scene_{scene_num:04d}_{best_ts_ms}.jpg"
        frame_path = os.path.join(output_dir, filename)
        success = cv2.imwrite(frame_path, best_frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        if not success:
            logger.error("Failed to write frame to disk: %s", frame_path)
            return None

        return {
            "scene_number": scene_num,
            "timestamp_ms": best_ts_ms,
            "frame_path": frame_path,
            "duration_ms": duration_ms,
            "sharpness_score": round(best_score, 4),
        }

    @staticmethod
    def _laplacian_variance(frame: "cv2.typing.MatLike") -> float:
        """Compute the Laplacian variance of a frame as a sharpness metric."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    async def delete_frames_for_video(self, video_id: str) -> None:
        """Delete all extracted frames for a given video_id from disk."""
        video_dir = os.path.join(self._frames_dir, video_id)
        if not os.path.isdir(video_dir):
            return
        try:
            import shutil
            await asyncio.to_thread(shutil.rmtree, video_dir)
            logger.info("Deleted frames directory for video %s", video_id)
        except Exception as exc:
            logger.warning(
                "Failed to delete frames directory for video %s: %s", video_id, exc
            )


frame_extractor_service = FrameExtractorService()

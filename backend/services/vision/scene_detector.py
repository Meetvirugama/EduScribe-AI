"""
Production-ready scene detection service using PySceneDetect.
Detects content-based scene boundaries in educational videos.
"""
import logging
import os
import asyncio
from typing import List, Dict, Any

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from core.config import settings

logger = logging.getLogger(__name__)


class SceneDetectionError(Exception):
    """Raised when scene detection fails."""


class SceneDetectorService:
    """
    Detects scene changes in video files using content-aware analysis.

    Uses PySceneDetect's ContentDetector which compares HSV histograms
    between adjacent frames to identify meaningful visual transitions
    (e.g., slide changes in lecture recordings).
    """

    def __init__(self) -> None:
        self._threshold: float = getattr(settings, "SCENE_DETECT_THRESHOLD", 27.0)
        self._min_scene_len: int = getattr(settings, "SCENE_MIN_LEN_FRAMES", 15)

    async def detect_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Detect scenes in a video file.

        Args:
            video_path: Absolute path to the video file.

        Returns:
            A list of scene dicts with keys:
                - scene_number (int)
                - start_time_ms (int)
                - end_time_ms (int)

        Raises:
            FileNotFoundError: If the video file does not exist.
            SceneDetectionError: If scene detection fails.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info("Starting scene detection for: %s", video_path)

        try:
            scenes = await asyncio.to_thread(self._run_detection, video_path)
        except Exception as exc:
            logger.error("Scene detection failed for %s: %s", video_path, exc)
            raise SceneDetectionError(f"Scene detection failed: {exc}") from exc

        logger.info("Detected %d scenes in %s", len(scenes), video_path)
        return scenes

    def _run_detection(self, video_path: str) -> List[Dict[str, Any]]:
        """Run PySceneDetect synchronously (called in a thread)."""
        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(
            ContentDetector(
                threshold=self._threshold,
                min_scene_len=self._min_scene_len,
            )
        )

        try:
            # Downscale improves speed with minimal accuracy loss
            video_manager.set_downscale_factor()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
        finally:
            video_manager.release()

        if not scene_list:
            logger.warning(
                "No scenes detected in %s. Treating whole video as single scene.", video_path
            )
            return self._single_scene_fallback(video_path)

        scenes: List[Dict[str, Any]] = []
        for i, (start_tc, end_tc) in enumerate(scene_list):
            scenes.append(
                {
                    "scene_number": i + 1,
                    "start_time_ms": int(start_tc.get_seconds() * 1000),
                    "end_time_ms": int(end_tc.get_seconds() * 1000),
                }
            )
        return scenes

    def _single_scene_fallback(self, video_path: str) -> List[Dict[str, Any]]:
        """
        When no scene cuts are found, return a single scene covering the full video.
        Uses OpenCV to probe total duration.
        """
        import cv2  # local import – OpenCV may not always be needed

        cap = cv2.VideoCapture(video_path)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            duration_ms = int((frame_count / fps) * 1000)
        finally:
            cap.release()

        if duration_ms <= 0:
            logger.warning("Could not determine video duration for %s", video_path)
            return []

        scenes = []
        chunk_duration_ms = 30000  # 30 seconds
        start_ms = 0
        scene_num = 1
        
        while start_ms < duration_ms:
            end_ms = min(start_ms + chunk_duration_ms, duration_ms)
            scenes.append({
                "scene_number": scene_num,
                "start_time_ms": start_ms,
                "end_time_ms": end_ms
            })
            start_ms = end_ms
            scene_num += 1

        logger.info("Chunked fallback into %d scenes (30s intervals)", len(scenes))
        return scenes


scene_detector_service = SceneDetectorService()

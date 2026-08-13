"""
Production-ready scene detection service using PySceneDetect.
Optimized via downscaling and caching.
"""
import logging
import os
import asyncio
from typing import List, Dict, Any

from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector
from core.config import settings

from services.vision.scene.optimizer import merge_short_scenes, generate_adaptive_fallback
from services.vision.scene.cache import scene_cache

logger = logging.getLogger(__name__)


class SceneDetectionError(Exception):
    """Raised when scene detection fails."""


class SceneDetectorService:
    def __init__(self) -> None:
        self._threshold: float = getattr(
            settings, "SCENE_DETECT_THRESHOLD", 25.0)

    async def detect_scenes(self, video_path: str,
                            video_id: str) -> List[Dict[str, Any]]:
        """
        Detect scenes in a video file utilizing aggressive optimization and caching.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 1. Cache lookup
        cached = scene_cache.get(video_id)
        if cached:
            logger.info(
                "Loaded %d scenes from cache for video %s",
                len(cached),
                video_id)
            return cached

        logger.info("Starting scene detection for: %s", video_path)

        # 2. Heavy CPU analysis
        try:
            scenes = await asyncio.to_thread(self._run_sync, video_path)
        except Exception as exc:
            logger.error("Scene detection failed for %s: %s", video_path, exc)
            raise SceneDetectionError(
                f"Scene detection failed: {exc}") from exc

        # 3. Post-processing
        if not scenes:
            scenes = await asyncio.to_thread(generate_adaptive_fallback, video_path)
        else:
            scenes = merge_short_scenes(scenes)

        scene_cache.set(video_id, scenes)
        logger.info(
            "Detected %d optimized scenes in %s",
            len(scenes),
            video_path)
        return scenes

    def _run_sync(self, video_path: str) -> List[Dict[str, Any]]:
        """Synchronous PySceneDetect execution – called inside a thread."""
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=self._threshold))

        # We downscale the video before scene detection because scene
        # boundaries are based on visual changes. Full resolution analysis
        # increases CPU cost but provides little improvement for slide
        # transition detection.
        frame_width = video.frame_size[0]
        if frame_width > 640:
            scene_manager.downscale = frame_width // 640

        scene_manager.detect_scenes(video, show_progress=False)
        scene_list = scene_manager.get_scene_list()

        scenes: List[Dict[str, Any]] = []
        for i, (start_tc, end_tc) in enumerate(scene_list):
            start_ms = int(start_tc.get_seconds() * 1000)
            end_ms = int(end_tc.get_seconds() * 1000)
            scenes.append({
                "scene_number": i + 1,
                "start_time_ms": start_ms,
                "end_time_ms": end_ms,
                "duration_ms": end_ms - start_ms,
                "frame_count": end_tc.get_frames() - start_tc.get_frames(),
                "scene_type": "detected_change",
                "detection_version": scene_cache.VERSION
            })
        return scenes


scene_detector_service = SceneDetectorService()

"""
Blur detection using Laplacian variance.
A frame is considered blurry if its Laplacian variance is below the configured threshold.
"""
import logging
from typing import List, Dict, Any

import cv2

from core.config import settings

logger = logging.getLogger(__name__)

# Frames with variance below this value are discarded
BLUR_THRESHOLD: float = getattr(settings, "BLUR_THRESHOLD", 100.0)


def compute_laplacian_variance(frame: "cv2.typing.MatLike") -> float:
    """
    Compute the Laplacian variance (focus measure) of an image.

    A higher value indicates a sharper image. Values below ~100 typically
    indicate motion blur or out-of-focus content.

    Args:
        frame: BGR image as numpy array.

    Returns:
        Float variance score.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(frame_path: str, threshold: float = BLUR_THRESHOLD) -> tuple[bool, float]:
    """
    Determine if a frame file is blurry.

    Args:
        frame_path: Absolute path to the image file.
        threshold:  Laplacian variance threshold. Frames below this are blurry.

    Returns:
        A tuple of (is_blurry: bool, score: float).

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image cannot be read.
    """
    if not __import__("os").path.exists(frame_path):
        raise FileNotFoundError(f"Frame image not found: {frame_path}")

    frame = cv2.imread(frame_path)
    if frame is None:
        raise ValueError(f"Could not decode image: {frame_path}")

    score = compute_laplacian_variance(frame)
    blurry = score < threshold
    if blurry:
        logger.debug("Frame blurry (score=%.2f, threshold=%.2f): %s", score, threshold, frame_path)
    return blurry, score


def filter_blurry_frames(
    frames: List[Dict[str, Any]],
    threshold: float = BLUR_THRESHOLD,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter a list of frame dicts, separating sharp from blurry frames.

    Each dict must contain a 'frame_path' key.

    Args:
        frames:    List of frame dicts.
        threshold: Blur threshold.

    Returns:
        Tuple of (sharp_frames, blurry_frames). Each dict in sharp_frames
        receives an extra 'blur_score' key.
    """
    sharp: List[Dict[str, Any]] = []
    blurry: List[Dict[str, Any]] = []

    for f in frames:
        path = f.get("frame_path", "")
        try:
            blurry_flag, score = is_blurry(path, threshold)
            enriched = {**f, "blur_score": round(score, 4)}
            if blurry_flag:
                blurry.append(enriched)
            else:
                sharp.append(enriched)
        except (FileNotFoundError, ValueError) as exc:
            logger.warning("Skipping frame during blur check (%s): %s", path, exc)
            blurry.append({**f, "blur_score": 0.0})

    logger.info(
        "Blur filter: %d sharp, %d blurry (threshold=%.2f)",
        len(sharp), len(blurry), threshold,
    )
    return sharp, blurry

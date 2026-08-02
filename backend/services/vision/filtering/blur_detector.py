"""
Blur detection using Laplacian variance.
Optimized for minimal CPU and memory footprint during long video processing.
"""
import logging
from typing import List, Dict, Any

import cv2
import numpy as np
from PIL import Image

from core.config import settings

logger = logging.getLogger(__name__)

# Frames with variance below this value are discarded
BLUR_THRESHOLD: float = getattr(settings, "BLUR_THRESHOLD", 100.0)

def compute_laplacian_variance(gray_frame: np.ndarray) -> float:
    """
    Compute the Laplacian variance (focus measure) of an image.
    
    # We explicitly use cv2.CV_16S (16-bit signed int) instead of CV_64F.
    # 8-bit image gradients comfortably fit in 16 bits. This reduces 
    # the memory footprint of the matrix by 4x, significantly improving
    # CPU cache locality and processing speed without losing precision.
    """
    laplacian = cv2.Laplacian(gray_frame, cv2.CV_16S)
    return float(laplacian.var())


def is_blurry(frame_path: str, threshold: float = BLUR_THRESHOLD) -> tuple[bool, float]:
    """
    Determine if a frame file is blurry using high-efficiency decoding.
    """
    if not __import__("os").path.exists(frame_path):
        raise FileNotFoundError(f"Frame image not found: {frame_path}")

    # We use Pillow's .draft() instead of cv2.imread().
    # Blur detection relies on high-frequency edges, not full 1080p resolution.
    # .draft('L', (256, 256)) tells libjpeg to decode directly to grayscale
    # and immediately downscale by dropping DCT coefficients. 
    # This bypasses the massive CPU cost of full decompression and cv2.cvtColor.
    try:
        img = Image.open(frame_path)
        img.draft("L", (256, 256))
        
        # In case the image is a format that didn't load as grayscale natively,
        # ensure it's L mode before converting to numpy
        if img.mode != "L":
            img = img.convert("L")
            
        gray_frame = np.array(img, dtype=np.uint8)
    except Exception as exc:
        raise ValueError(f"Could not decode image {frame_path}: {exc}") from exc

    score = compute_laplacian_variance(gray_frame)
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
        
        # We reuse the pre-calculated blur_score from the extraction phase.
        # This completely eliminates disk I/O and CPU overhead in this step.
        if "blur_score" in f:
            score = f["blur_score"]
            blurry_flag = score < threshold
            enriched = f
            if blurry_flag:
                blurry.append(enriched)
            else:
                sharp.append(enriched)
            continue
            
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

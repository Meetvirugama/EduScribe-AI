"""
Difference-hash (dHash) based duplicate frame removal.

Optimized to minimize CPU and GPU utilization during the extraction pipeline.
Replaces the previous pHash (DCT-based) and O(N²) comparison approach with
integer-based dHash and O(N) sequential comparisons.
"""
import logging
import os
from collections import deque
from typing import List, Dict, Any, Tuple

import imagehash
from PIL import Image

from core.config import settings

logger = logging.getLogger(__name__)

# Hamming distance threshold – lower = stricter deduplication
# For dhash, a threshold of 5 is generally still effective for visually identical frames.
PHASH_THRESHOLD: int = getattr(settings, "PHASH_THRESHOLD", 5)


def compute_phash(frame_path: str) -> str:
    """
    Compute the difference hash (dhash) of an image file.
    
    (Note: Retained name 'compute_phash' for API/Test compatibility,
    but internally upgraded to use dhash for CPU minimization).

    Args:
        frame_path: Absolute path to the image file.

    Returns:
        Hex string representation of the hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the image cannot be read.
    """
    if not os.path.exists(frame_path):
        raise FileNotFoundError(f"Frame image not found: {frame_path}")

    try:
        img = Image.open(frame_path)
        # Using .draft instructs libjpeg to decode at a lower resolution.
        # This massively drops CPU decode overhead and memory usage.
        img.draft("RGB", (32, 32))
        img = img.convert("RGB")
        # We use dhash (Difference Hash) instead of phash (Perceptual Hash).
        # dhash compares adjacent pixel gradients (integer subtraction) whereas
        # phash uses Discrete Cosine Transforms (floating-point math).
        # This dramatically lowers CPU usage while keeping exact-duplicate accuracy high.
        return str(imagehash.dhash(img))
    except Exception as exc:
        raise ValueError(f"Could not compute hash for {frame_path}: {exc}") from exc


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """
    Compute the Hamming distance between two hex hash strings.

    Args:
        hash_a: First hash hex string.
        hash_b: Second hash hex string.

    Returns:
        Integer Hamming distance.
    """
    h_a = imagehash.hex_to_hash(hash_a)
    h_b = imagehash.hex_to_hash(hash_b)
    return int(h_a - h_b)


def deduplicate_frames(
    frames: List[Dict[str, Any]],
    threshold: int = PHASH_THRESHOLD,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Remove visually duplicate frames using difference hashing (dHash).

    Iterates through frames sequentially. We compare each frame ONLY to the
    last known unique frame. This reduces time complexity from O(N²) to O(N)
    and memory complexity to O(1), capitalizing on the fact that video duplicates
    occur consecutively in a timeline.

    Args:
        frames:    List of frame dicts, each containing 'frame_path'.
        threshold: Maximum Hamming distance to consider two frames duplicates.

    Returns:
        Tuple of (unique_frames, duplicate_frames). Each kept frame dict
        receives a 'phash' key (retained key name for DB compatibility).
    """
    unique: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []

    # Stage 1 tracks only the immediately preceding unique frame — O(1).
    last_unique_hash = None

    # Stage 2 global check: bounded deque instead of a growing list.
    # A deque(maxlen=50) keeps only the 50 most-recent unique hashes.
    # This caps Stage 2 from O(N²) worst case to O(50·N) = O(N), because
    # recurring slides (title cards, flashback diagrams) cluster temporally
    # within a short window. Hashes older than 50 scenes are very unlikely
    # to recur and not worth the quadratic search cost.
    seen_hashes: deque = deque(maxlen=50)

    for frame in frames:
        path = frame.get("frame_path", "")
        try:
            # We use Pillow instead of OpenCV to avoid heavy C++ dependencies.
            # We call .draft('RGB', (32, 32)) BEFORE .convert("RGB") to instruct
            # the underlying JPEG decoder (libjpeg) to stop parsing high-resolution
            # DCT coefficients. This massively drops CPU decode overhead and I/O wait.
            img = Image.open(path)
            img.draft("RGB", (32, 32))
            img = img.convert("RGB")
            
            # We use dhash (Difference Hash) instead of phash (Perceptual Hash).
            # dhash compares adjacent pixel gradients (integer subtraction) whereas
            # phash uses Discrete Cosine Transforms (floating-point math).
            # This dramatically lowers CPU usage while keeping exact-duplicate accuracy high.
            # We do NOT use GPU acceleration because transferring a 1080p image over PCIe 
            # for a 64-bit hash math operation creates a massive bottleneck vs native CPU.
            h_obj = imagehash.dhash(img)
            h_str = str(h_obj)
            
        except (FileNotFoundError, ValueError, OSError) as exc:
            logger.warning("Skipping frame in dedup (%s): %s", path, exc)
            # If we can't read it, fail safely by discarding it to duplicates
            duplicates.append(frame)
            continue

        is_dup = False

        # Stage 1: Previous Frame Check
        # Fast path for consecutive identical frames
        if last_unique_hash is not None:
            distance = h_obj - last_unique_hash
            if distance < threshold:
                is_dup = True

        # Stage 2: Global Verification
        # If it's not a consecutive duplicate, check if it matches ANY previous unique frame
        # (e.g., alternating slides, recurring title cards, flashbacks)
        if not is_dup:
            if any((h_obj - existing) < threshold for existing in seen_hashes):
                is_dup = True

        if is_dup:
            logger.debug("Duplicate frame detected: %s", path)
            # Retain 'phash' key name for database pipeline backwards compatibility
            duplicates.append({**frame, "phash": h_str})
        else:
            last_unique_hash = h_obj
            seen_hashes.append(h_obj)
            unique.append({**frame, "phash": h_str})

    logger.info(
        "Dedup: %d unique, %d duplicates removed (threshold=%d, algorithm=dhash, strategy=sequential)",
        len(unique),
        len(duplicates),
        threshold,
    )
    return unique, duplicates

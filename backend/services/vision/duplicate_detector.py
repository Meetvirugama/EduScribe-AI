"""
Perceptual-hash based duplicate frame removal.

Uses pHash (DCT-based perceptual hash) from the `imagehash` library.
Two frames are considered duplicates when their Hamming distance is
below the configured threshold.
"""
import logging
import os
from typing import List, Dict, Any, Tuple

import imagehash
from PIL import Image

from core.config import settings

logger = logging.getLogger(__name__)

# Hamming distance threshold – lower = stricter deduplication
PHASH_THRESHOLD: int = getattr(settings, "PHASH_THRESHOLD", 5)


def compute_phash(frame_path: str) -> str:
    """
    Compute the perceptual hash of an image file.

    Args:
        frame_path: Absolute path to the image file.

    Returns:
        Hex string representation of the pHash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the image cannot be read.
    """
    if not os.path.exists(frame_path):
        raise FileNotFoundError(f"Frame image not found: {frame_path}")

    try:
        img = Image.open(frame_path).convert("RGB")
        return str(imagehash.phash(img))
    except Exception as exc:
        raise ValueError(f"Could not compute pHash for {frame_path}: {exc}") from exc


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """
    Compute the Hamming distance between two hex pHash strings.

    Args:
        hash_a: First pHash hex string.
        hash_b: Second pHash hex string.

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
    Remove visually duplicate frames using perceptual hashing.

    Iterates through frames in order. The first occurrence of a unique
    visual is kept; subsequent near-identical frames are discarded.

    Args:
        frames:    List of frame dicts, each containing 'frame_path'.
        threshold: Maximum Hamming distance to consider two frames duplicates.

    Returns:
        Tuple of (unique_frames, duplicate_frames). Each kept frame dict
        receives a 'phash' key.
    """
    unique: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []
    seen_hashes: List[str] = []

    for frame in frames:
        path = frame.get("frame_path", "")
        try:
            ph = compute_phash(path)
        except (FileNotFoundError, ValueError) as exc:
            logger.warning("Skipping frame in dedup (%s): %s", path, exc)
            duplicates.append(frame)
            continue

        is_dup = any(
            hamming_distance(ph, existing) < threshold for existing in seen_hashes
        )

        if is_dup:
            logger.debug("Duplicate frame detected: %s", path)
            duplicates.append({**frame, "phash": ph})
        else:
            seen_hashes.append(ph)
            unique.append({**frame, "phash": ph})

    logger.info(
        "Dedup: %d unique, %d duplicates removed (threshold=%d)",
        len(unique),
        len(duplicates),
        threshold,
    )
    return unique, duplicates

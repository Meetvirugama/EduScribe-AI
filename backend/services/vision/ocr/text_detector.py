"""
Cheap CPU-based text detection to prevent wasting GPU resources.
"""
import cv2
import logging

logger = logging.getLogger(__name__)


def has_meaningful_text(frame_path: str) -> bool:
    """
    Uses edge density to determine if text exists.
    """
    img = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False

    # Calculate edge density using Sobel
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    edge_density = (sobelx**2 + sobely**2).mean()

    # If density is extremely low, there are no sharp edges (no text)
    has_text = edge_density > 50.0
    if not has_text:
        logger.debug(
            "Skipping OCR for %s: no meaningful text edges detected.",
            frame_path)
    return has_text

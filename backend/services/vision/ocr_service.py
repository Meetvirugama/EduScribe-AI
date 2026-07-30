"""
OCR service using PaddleOCR for local text extraction from video frames.

Extracts text including titles, bullet points, code blocks, equations, and tables
from slide images with confidence scoring and output cleaning.
"""
import asyncio
import logging
import os
import re
from typing import List, Dict, Any

from core.config import settings

logger = logging.getLogger(__name__)

# Minimum confidence score to include OCR text
OCR_MIN_CONFIDENCE: float = getattr(settings, "OCR_MIN_CONFIDENCE", 0.70)


class OCRServiceError(Exception):
    """Raised when OCR processing fails."""


class OCRService:
    """
    Wraps PaddleOCR for text extraction from educational slide frames.

    PaddleOCR is loaded lazily on first use to avoid slowing application startup.
    Thread-safety note: PaddleOCR's predict() method is not thread-safe when using
    GPU. Since this service runs inside asyncio.to_thread, a single instance is
    used with a per-call lock to prevent concurrent access.
    """

    def __init__(self) -> None:
        self._ocr = None
        self._lock = asyncio.Lock()

    def _get_ocr(self):
        """Lazy-load PaddleOCR model."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR  # noqa: PLC0415
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="en"
                )
                logger.info("PaddleOCR model loaded successfully.")
            except ImportError as exc:
                raise OCRServiceError(
                    "PaddleOCR is not installed. Run: pip install paddlepaddle paddleocr"
                ) from exc
        return self._ocr

    async def extract_text(self, frame_path: str) -> Dict[str, Any]:
        """
        Extract text from a single image file.

        Args:
            frame_path: Absolute path to the image file.

        Returns:
            Dict with keys:
                - raw_text (str): All text lines joined with newlines.
                - clean_text (str): Deduplicated, cleaned version.
                - average_confidence (float): Mean confidence across all text blocks.
                - line_count (int): Number of text lines found.

        Raises:
            FileNotFoundError: If the image file does not exist.
            OCRServiceError: If OCR processing fails.
        """
        if not os.path.exists(frame_path):
            raise FileNotFoundError(f"Frame not found for OCR: {frame_path}")

        async with self._lock:
            try:
                result = await asyncio.to_thread(self._run_ocr, frame_path)
            except OCRServiceError:
                raise
            except Exception as exc:
                logger.error("Unexpected OCR error for %s: %s", frame_path, exc)
                raise OCRServiceError(f"OCR failed for {frame_path}: {exc}") from exc

        return result

    def _run_ocr(self, frame_path: str) -> Dict[str, Any]:
        """Synchronous OCR execution – called inside a thread."""
        ocr = self._get_ocr()
        ocr_result = ocr.predict(frame_path)

        lines: List[str] = []
        confidences: List[float] = []

        # PaddleOCR returns a list of results per image; we process the first (and only)
        if ocr_result and isinstance(ocr_result, list):
            # Newer PaddleOCR (≥2.7) returns Result objects; older returns dicts
            for item in ocr_result:
                if item is None:
                    continue
                # Handle list-of-lists format from older API
                if isinstance(item, list):
                    for block in item:
                        text, conf = self._parse_ocr_block(block)
                        if text and conf >= OCR_MIN_CONFIDENCE:
                            lines.append(text)
                            confidences.append(conf)
                else:
                    # Newer API: item is a dict-like object with .rec_texts and .rec_scores
                    rec_texts = getattr(item, "rec_texts", []) or []
                    rec_scores = getattr(item, "rec_scores", []) or []
                    for text, score in zip(rec_texts, rec_scores):
                        if text and score >= OCR_MIN_CONFIDENCE:
                            lines.append(text.strip())
                            confidences.append(float(score))

        raw_text = "\n".join(lines)
        clean_text = self._clean_text("\n".join(dict.fromkeys(lines)))  # preserve order dedup
        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

        logger.debug(
            "OCR result for %s: %d lines, avg_conf=%.3f", frame_path, len(lines), avg_conf
        )

        return {
            "raw_text": raw_text,
            "clean_text": clean_text,
            "average_confidence": avg_conf,
            "line_count": len(lines),
        }

    @staticmethod
    def _parse_ocr_block(block: Any) -> tuple[str, float]:
        """Parse a single OCR result block into (text, confidence)."""
        try:
            if isinstance(block, (list, tuple)) and len(block) == 2:
                _bbox, (text, conf) = block
                return str(text).strip(), float(conf)
        except (TypeError, ValueError, IndexError):
            pass
        return "", 0.0

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean raw OCR output by removing noise while preserving structure.

        - Strips excessive whitespace.
        - Removes isolated single-character lines (often OCR noise).
        - Normalises Unicode dashes and quotes.
        """
        lines = text.splitlines()
        cleaned: List[str] = []
        for line in lines:
            stripped = line.strip()
            # Remove likely noise: single char or only punctuation
            if len(stripped) <= 1 and not stripped.isdigit():
                continue
            # Normalise common OCR substitutions
            stripped = stripped.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
            stripped = re.sub(r"\s{2,}", " ", stripped)
            cleaned.append(stripped)
        return "\n".join(cleaned)


ocr_service = OCRService()

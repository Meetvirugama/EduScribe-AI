"""
OCR service using PaddleOCR for local text extraction from video frames.
Optimized for low GPU memory usage, lazy loading, and caching.
"""
import asyncio
import logging
import os
import re
import cv2
from typing import List, Dict, Any

from core.config import settings
from services.vision.ocr.cache import ocr_cache
from services.vision.ocr.text_detector import has_meaningful_text
from services.vision.ocr.features import generate_ocr_features

logger = logging.getLogger(__name__)

# Minimum confidence score to include OCR text
OCR_MIN_CONFIDENCE: float = getattr(settings, "OCR_MIN_CONFIDENCE", 0.70)


class OCRServiceError(Exception):
    """Raised when OCR processing fails."""


class OCRService:
    def __init__(self) -> None:
        self._ocr = None
        
        # A single OCR inference path is used because concurrent GPU
        # inference can increase memory pressure and create unstable behavior.
        self._lock = asyncio.Lock()

    def _get_ocr(self):
        """
        PaddleOCR model is loaded only when required.
        Loading during application startup increases initial
        memory usage and delays service readiness.
        """
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR  # noqa: PLC0415
                self._ocr = PaddleOCR(use_angle_cls=True, lang="en")
                logger.info("PaddleOCR model loaded successfully.")
            except ImportError as exc:
                raise OCRServiceError(
                    "PaddleOCR is not installed. Run: pip install paddlepaddle paddleocr"
                ) from exc
        return self._ocr

    def _resize_for_ocr(self, img):
        """
        We resize frames before OCR because slide text remains readable
        at this resolution while reducing GPU memory usage.
        Full-resolution OCR was rejected because it increases inference
        cost without significant accuracy improvement for this use case.
        """
        h, w = img.shape[:2]
        if w > 1280:
            scale = 1280 / float(w)
            img = cv2.resize(img, (1280, int(h * scale)))
        return img

    async def extract_text(self, frame_path: str) -> Dict[str, Any]:
        """
        Extract text and reusable numerical features from a single image file.
        """
        if not os.path.exists(frame_path):
            raise FileNotFoundError(f"Frame not found for OCR: {frame_path}")

        # 1. Check cache first
        cached = ocr_cache.get(frame_path)
        if cached:
            return cached

        # 2. Fast CPU text presence filter
        # Only run expensive GPU inference if there are text-like edges
        has_text = await asyncio.to_thread(has_meaningful_text, frame_path)
        if not has_text:
            empty_result = {
                "raw_text": "",
                "clean_text": "",
                **generate_ocr_features("", 0.0, 0)
            }
            ocr_cache.set(frame_path, empty_result)
            return empty_result

        # 3. Locked GPU inference
        async with self._lock:
            try:
                result = await asyncio.to_thread(self._run_ocr_sync, frame_path)
                ocr_cache.set(frame_path, result)
                return result
            except OCRServiceError:
                raise
            except Exception as exc:
                logger.error("Unexpected OCR error for %s: %s", frame_path, exc)
                raise OCRServiceError(f"OCR failed for {frame_path}: {exc}") from exc

    def _run_ocr_sync(self, frame_path: str) -> Dict[str, Any]:
        """Synchronous OCR execution – called inside a thread."""
        ocr = self._get_ocr()
        
        # Read and resize
        img = cv2.imread(frame_path)
        img = self._resize_for_ocr(img)
        
        ocr_result = ocr.predict(img)

        lines: List[str] = []
        confidences: List[float] = []

        if ocr_result and isinstance(ocr_result, list):
            for item in ocr_result:
                if item is None:
                    continue
                if isinstance(item, list):
                    for block in item:
                        text, conf = self._parse_ocr_block(block)
                        if text and conf >= OCR_MIN_CONFIDENCE:
                            lines.append(text)
                            confidences.append(conf)
                else:
                    rec_texts = getattr(item, "rec_texts", []) or []
                    rec_scores = getattr(item, "rec_scores", []) or []
                    for text, score in zip(rec_texts, rec_scores):
                        if text and score >= OCR_MIN_CONFIDENCE:
                            lines.append(text.strip())
                            confidences.append(float(score))

        raw_text = "\n".join(lines)
        clean_text = self._clean_text("\n".join(dict.fromkeys(lines)))
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        # Generate numerical features once and cache them flat
        features = generate_ocr_features(clean_text, avg_conf, len(lines))
        
        logger.debug(
            "OCR result for %s: %d lines, avg_conf=%.3f", frame_path, len(lines), avg_conf
        )

        return {
            "raw_text": raw_text,
            "clean_text": clean_text,
            **features
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
        """
        lines = text.splitlines()
        cleaned: List[str] = []
        for line in lines:
            stripped = line.strip()
            # Remove likely noise: single char or only punctuation
            if len(stripped) <= 1 and not stripped.isdigit():
                continue
            stripped = stripped.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
            stripped = re.sub(r"\s{2,}", " ", stripped)
            cleaned.append(stripped)
        return "\n".join(cleaned)


ocr_service = OCRService()

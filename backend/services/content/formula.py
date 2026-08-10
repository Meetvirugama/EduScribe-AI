"""
services/content/formula.py — Formula Sheet Generator

Generates a structured formula sheet from equations detected in OCR frames
and mentioned in the lecture transcript.

Issue Resolved: #12 (notes generation not modular — missing formula generator)
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)


class FormulaSheetGenerator(BaseContentService):
    """
    Generates formula sheets by extracting mathematical expressions
    from both the transcript and OCR-extracted slide text.
    """

    def _format_timestamp(self, time_sec: float) -> str:
        """Format seconds into HH:MM:SS string."""
        if time_sec is None:
            return "00:00:00"
        m, s = divmod(int(time_sec), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _is_math_formula(self, text: str) -> bool:
        """
        Conservatively detect if text contains mathematical formulas.
        Avoids treating simple hyphens as math.
        """
        # Specific math symbols that strongly indicate a formula
        strong_symbols = ["∑", "∫", "√", "²", "³", "∂", "≤", "≥", "≈", "≠"]
        if any(sym in text for sym in strong_symbols):
            return True
        
        # Look for equations (requires an equals sign and other operands)
        if "=" in text:
            # Check if there are math operators around the equals sign, 
            # or variable-like structures (e.g. F = ma)
            if re.search(r"[\+\-\*\/\^]", text) or re.search(r"\b[A-Za-z]+\s*=\s*[A-Za-z0-9]", text):
                return True
                
        # Expressions with clear math operators but no equals (e.g. polynomial)
        if re.search(r"\b[A-Za-z0-9]+\s*[\+\-\*\/]\s*[A-Za-z0-9]+\b", text) and not re.search(r"^[A-Za-z\s\-]+$", text):
            # The second condition prevents pure text like "Non-linear regression - introduction"
            # We want actual variables/numbers mixed with operators
            return True
            
        return False

    async def generate_formula_sheet(self, context: LectureContext) -> Dict[str, Any]:
        """
        Generate a structured formula sheet from the LectureContext.
        """
        logger.info("Generating formula sheet...")
        empty_result = {"formulas": [], "notation_guide": {}, "topic_groups": {}}

        # Reconstruct transcript with timestamps to preserve source location
        transcript_lines = []
        for s in context.segments:
            start_time = s.get("start")
            text = s.get("text", "").strip()
            if text:
                ts = self._format_timestamp(start_time) if start_time is not None else "Unknown"
                transcript_lines.append(f"[{ts}] {text}")
        
        transcript_context = "\n".join(transcript_lines)
        if not transcript_context.strip():
            transcript_context = "No transcript provided."

        # Extract OCR text containing mathematical notation
        ocr_formulas = []
        for frame in context.frames:
            ocr = frame.get("ocr", "")
            if ocr and self._is_math_formula(ocr):
                time_sec = frame.get("time_sec", 0)
                ts = self._format_timestamp(time_sec)
                ocr_formulas.append(f"[{ts}] (slide): {ocr}")

        ocr_context = "\n".join(ocr_formulas[:20]) if ocr_formulas else "No formula slides detected."

        messages = self._render_messages(
            system_msg="You are a mathematical content extractor. Output only valid JSON.",
            template_name="formula_sheet",
            transcript_context=transcript_context,
            ocr_context=ocr_context
        )

        try:
            response = await self.llm_manager.generate(TaskType.FORMULA_EXPLANATION, messages)
            
            # _safe_dump handles both Pydantic Models and JSON fallback extraction
            raw_dict = self._safe_dump(response, fallback=empty_result)
            
            # Validate with Pydantic if not already a FormulasOutput
            from ..llm.validation.schemas.notes import FormulasOutput
            parsed = FormulasOutput(**raw_dict)
            
            # Ensure topic groups only reference valid formulas
            formula_names = {f.name for f in parsed.formulas}
            valid_topic_groups = {}
            for topic, f_list in parsed.topic_groups.items():
                valid_f_list = [f_name for f_name in f_list if f_name in formula_names]
                if valid_f_list:
                    valid_topic_groups[topic] = valid_f_list
            parsed.topic_groups = valid_topic_groups
            
            return parsed.model_dump()
            
        except Exception as exc:
            logger.error("FormulaService: generation failed: %s", exc)
            return empty_result

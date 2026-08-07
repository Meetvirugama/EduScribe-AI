"""
services/content/formula_service.py — Formula Sheet Generator

Generates a structured formula sheet from equations detected in OCR frames
and mentioned in the lecture transcript.

Issue Resolved: #12 (notes generation not modular — missing formula generator)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FormulaService:
    """
    Generates formula sheets by extracting mathematical expressions
    from both the transcript and OCR-extracted slide text.
    """

    def __init__(self, llm_manager=None) -> None:
        self.llm_manager = llm_manager

    async def generate_formula_sheet(
        self,
        transcript_segments: List[Dict[str, Any]],
        frames_data: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured formula sheet.

        Returns:
            {
              "formulas": [
                {
                  "name": "Formula name",
                  "expression": "E = mc²",
                  "variables": {"E": "Energy", "m": "Mass", "c": "Speed of light"},
                  "context": "When to apply this formula",
                  "source": "transcript|ocr",
                  "timestamp": "HH:MM:SS"
                }
              ],
              "notation_guide": {"symbol": "meaning"},
              "topic_groups": {"Topic Name": ["formula1", "formula2"]}
            }
        """
        if not self.llm_manager:
            return {"formulas": [], "notation_guide": {}, "topic_groups": {}}

        transcript_text = " ".join(s.get("text", "") for s in transcript_segments)

        # Extract OCR text containing mathematical notation
        ocr_formulas = []
        for frame in (frames_data or []):
            ocr = frame.get("ocr", "")
            if ocr and any(sym in ocr for sym in ["=", "+", "-", "×", "∑", "∫", "√", "²", "³"]):
                time_sec = frame.get("time_sec", 0)
                m, s = divmod(int(time_sec), 60)
                h, m = divmod(m, 60)
                ocr_formulas.append(f"[{h:02d}:{m:02d}:{s:02d}] (slide): {ocr}")

        ocr_context = "\n".join(ocr_formulas[:20]) if ocr_formulas else "No formula slides detected."

        prompt = f"""You are an expert at extracting mathematical and scientific formulas from lecture content.

Analyze the following transcript and slide text. Extract ALL formulas, equations, and mathematical expressions.

Output ONLY valid JSON:
{{
    "formulas": [
        {{
            "name": "Formula name (e.g. Newton's Second Law)",
            "expression": "F = ma",
            "variables": {{"F": "Force (N)", "m": "Mass (kg)", "a": "Acceleration (m/s²)"}},
            "context": "When and how to apply this formula",
            "source": "transcript or ocr",
            "timestamp": "HH:MM:SS or null"
        }}
    ],
    "notation_guide": {{"symbol": "meaning"}},
    "topic_groups": {{"Topic Name": ["formula_name_1", "formula_name_2"]}}
}}

Slide text with formulas:
{ocr_context}

Transcript:
{transcript_text[:6000]}"""

        try:
            from services.llm.model_selector import TaskType
            messages = [
                {"role": "system", "content": "You are a mathematical content extractor. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ]
            response = await self.llm_manager.generate(TaskType.FORMULA_EXPLANATION, messages)
            raw = getattr(response, "text", None) or str(response)

            import re, json
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as exc:
            logger.error("FormulaService: generation failed: %s", exc)

        return {"formulas": [], "notation_guide": {}, "topic_groups": {}}

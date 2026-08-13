"""
services/content/formula.py — Formula Sheet Generator

Generates a structured formula sheet from equations detected in OCR frames
and mentioned in the lecture transcript.

Issue Resolved: #12 (notes generation not modular — missing formula generator)
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

from .base import BaseContentService
from .context import LectureContext


logger = logging.getLogger(__name__)


class FormulaSheetGenerator(BaseContentService):
    """
    Generates formula sheets by extracting mathematical expressions
    from both the transcript and OCR-extracted slide text.
    """

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
            if re.search(
                    r"[\+\-\*\/\^]", text) or re.search(r"\b[A-Za-z]+\s*=\s*[A-Za-z0-9]", text):
                return True

        # Expressions with clear math operators but no equals (e.g. polynomial)
        if re.search(r"\b[A-Za-z0-9]+\s*[\+\-\*\/]\s*[A-Za-z0-9]+\b",
                     text) and not re.search(r"^[A-Za-z\s\-]+$", text):
            # The second condition prevents pure text like "Non-linear regression - introduction"
            # We want actual variables/numbers mixed with operators
            return True

        return False

    async def generate_formula_sheet(
            self, context: LectureContext) -> Dict[str, Any]:
        """
        Generate a structured formula sheet from the LectureContext.
        """
        import time
        start_time = time.time()

        logger.info("Generating formula sheet...")
        empty_result = {
            "formulas": [],
            "notation_guide": {},
            "topic_groups": {}}

        try:
            # 1. Chunk Transcript
            video_id = context.metadata.get("video_id", "default_video")
            chunks = self._chunk_segments_with_ocr(context, video_id, use_semantic_chunking=False)

            # 2. Extract OCR formulas and map to chunks
            ocr_formulas_by_chunk = {c["chunk_id"]: [] for c in chunks}
            for frame in context.frames:
                ocr = frame.get("ocr", "")
                if ocr and self._is_math_formula(ocr):
                    time_sec = frame.get("time_sec", 0)
                    # Find which chunk this belongs to
                    assigned = False
                    for c in chunks:
                        if c["start_time"] <= time_sec <= c["end_time"]:
                            ocr_formulas_by_chunk[c["chunk_id"]].append(ocr)
                            assigned = True
                            break
                    if not assigned and chunks:
                        ocr_formulas_by_chunk[chunks[0]
                                              ["chunk_id"]].append(ocr)

            # 3. Process each chunk sequentially to avoid Rate Limits on large
            # videos
            from ..llm.validation.schemas.notes import FormulasOutput

            all_formulas = []
            global_notation_guide = {}
            global_topic_groups = {}

            final_provider = "unknown"
            final_model = "unknown"
            total_latency = 0.0
            total_tokens = 0

            from ..llm.model_selector import TaskType

            for c in chunks:
                chunk_id = c["chunk_id"]
                chunks_context = f"[{chunk_id} | {c['start_time']} - {c['end_time']}] {c['text']}"

                ocr_formulas = ocr_formulas_by_chunk.get(chunk_id, [])
                ocr_context = "\n".join(
                    [f"(slide): {f}" for f in ocr_formulas]) if ocr_formulas else "No formula slides detected in this chunk."

                messages = self._render_messages(
                    system_msg="You are a mathematical content extractor. Output only valid JSON.",
                    template_name="formula_sheet",
                    chunks_context=chunks_context,
                    ocr_context=ocr_context
                )

                try:
                    # Add tiny sleep to help with rate limits
                    import asyncio
                    await asyncio.sleep(0.5)

                    response = await self.llm_manager.generate(TaskType.FORMULA_EXPLANATION, messages)

                    if hasattr(response,
                               "provider") and response.provider != "unknown":
                        final_provider = response.provider
                    if hasattr(response,
                               "model") and response.model != "unknown":
                        final_model = response.model
                    if hasattr(response, "latency"):
                        total_latency += response.latency
                    if hasattr(response, "total_tokens"):
                        total_tokens += response.total_tokens

                    raw_dict = self._safe_dump(
                        response,
                        fallback={
                            "formulas": [],
                            "notation_guide": {},
                            "topic_groups": {}})
                    parsed = FormulasOutput(**raw_dict)

                    # Aggregate Formulas
                    for f_item in parsed.formulas:
                        # Enforce the source mapping
                        if not f_item.sources:
                            from ..llm.validation.schemas.notes import SourceReferenceItem
                            f_item.sources = [SourceReferenceItem(
                                chunk_id=chunk_id,
                                timestamp_start=c['start_time'],
                                timestamp_end=c['end_time']
                            )]
                        else:
                            for src in f_item.sources:
                                src.timestamp_start = c['start_time']
                                src.timestamp_end = c['end_time']
                        all_formulas.append(f_item)

                    # Merge notation guide
                    if parsed.notation_guide:
                        for k, v in parsed.notation_guide.items():
                            if k not in global_notation_guide:
                                global_notation_guide[k] = v

                    # Merge topic groups
                    if parsed.topic_groups:
                        for topic, f_list in parsed.topic_groups.items():
                            if topic not in global_topic_groups:
                                global_topic_groups[topic] = []
                            global_topic_groups[topic].extend(f_list)

                except Exception as inner_exc:
                    logger.warning(
                        f"Failed to extract formula for chunk {chunk_id}: {inner_exc}")

            # 4. Final Validation & Cleanup
            formula_names = {f.name for f in all_formulas}
            valid_topic_groups = {}
            for topic, f_list in global_topic_groups.items():
                valid_f_list = list(
                    set([f_name for f_name in f_list if f_name in formula_names]))
                if valid_f_list:
                    valid_topic_groups[topic] = valid_f_list

            final_parsed = FormulasOutput(
                formulas=all_formulas,
                notation_guide=global_notation_guide,
                topic_groups=valid_topic_groups,
                provider=final_provider,
                model=final_model,
                latency=round(total_latency, 2),
                total_tokens=total_tokens
            )

            execution_time = round(time.time() - start_time, 2)
            return {
                "status": "success",
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": final_parsed.model_dump(exclude_none=True)
            }

        except Exception as exc:
            logger.error("FormulaService: generation failed: %s", exc)
            execution_time = round(
                time.time() - start_time,
                2) if 'start_time' in locals() else 0.0
            return {
                "status": "error",
                "error": str(exc),
                "metadata": {
                    "execution_time_sec": execution_time
                },
                "data": empty_result
            }

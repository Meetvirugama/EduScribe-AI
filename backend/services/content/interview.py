"""
services/content/interview.py — Interview & Viva Question Generator

Generates structured interview questions, viva voce questions, and exam
preparation materials from the lecture content.

Issue Resolved: #12 (notes generation not modular — missing interview generator)
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType

logger = logging.getLogger(__name__)


class InterviewGenerator(BaseContentService):
    """Generates technical and conceptual interview questions."""

    async def generate_interview_questions(
            self, context: LectureContext) -> Dict[str, Any]:
        """
        Generate interview/viva questions.
        """
        logger.info("Generating interview questions...")

        empty_result = {
            "technical_questions": [],
            "conceptual_questions": [],
            "scenario_questions": [],
            "viva_questions": [],
            "difficulty_breakdown": {"easy": 0, "medium": 0, "hard": 0}
        }

        if not self.llm_manager:
            return empty_result

        # Map numeric difficulty from context to a string descriptor if present
        diff_level = getattr(context.input, "difficulty", 3)
        difficulty_str = "mixed"
        if diff_level <= 2:
            difficulty_str = "easy"
        elif diff_level >= 4:
            difficulty_str = "hard"
        else:
            difficulty_str = "medium"

        learning_note = context.detailed_notes_md
        if not learning_note.strip():
            logger.warning(
                "InterviewGenerator: detailed_notes_md is empty. Falling back to transcript.")
            learning_note = context.transcript

        messages = self._render_messages(
            system_msg="You are an expert interview question generator. Output only valid JSON.",
            template_name="interview",
            learning_note=learning_note,
            difficulty=difficulty_str
        )

        try:
            # INTERVIEW_PERSPECTIVE is the correct TaskType as per
            # model_selector.py
            response = await self.llm_manager.generate(TaskType.INTERVIEW_PERSPECTIVE, messages)

            raw_dict = self._safe_dump(response, fallback=empty_result)

            # Optionally validate explicitly to ensure it matches the schema
            from ..llm.validation.schemas.notes import InterviewOutput
            parsed = InterviewOutput(**raw_dict)

            # Recalculate difficulty breakdown accurately
            easy = sum(
                1 for q in parsed.technical_questions +
                parsed.conceptual_questions +
                parsed.scenario_questions if q.difficulty.lower() == "easy")
            medium = sum(
                1 for q in parsed.technical_questions +
                parsed.conceptual_questions +
                parsed.scenario_questions if q.difficulty.lower() == "medium")
            hard = sum(
                1 for q in parsed.technical_questions +
                parsed.conceptual_questions +
                parsed.scenario_questions if q.difficulty.lower() == "hard")

            parsed.difficulty_breakdown = {
                "easy": easy, "medium": medium, "hard": hard}

            return parsed.model_dump()

        except Exception as exc:
            logger.error("InterviewService: generation failed: %s", exc)
            return empty_result

"""
services/content/interview_service.py — Interview & Viva Question Generator

Generates structured interview questions, viva voce questions, and exam
preparation materials from the lecture content.

Issue Resolved: #12 (notes generation not modular — missing interview generator)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class InterviewService:
    """Generates interview and viva questions from lecture concepts."""

    def __init__(self, llm_manager=None) -> None:
        self.llm_manager = llm_manager

    async def generate_interview_questions(
        self,
        transcript_segments: List[Dict[str, Any]],
        concepts_data: Dict[str, Any] = None,
        difficulty: str = "mixed",
    ) -> Dict[str, Any]:
        """
        Generate interview/viva questions.

        Returns:
            {
              "technical_questions": [...],
              "conceptual_questions": [...],
              "scenario_questions": [...],
              "viva_questions": [...],
              "difficulty_breakdown": {"easy": N, "medium": N, "hard": N}
            }
        """
        if not self.llm_manager:
            return {"technical_questions": [], "conceptual_questions": [], "viva_questions": []}

        transcript_text = " ".join(s.get("text", "") for s in transcript_segments)
        concepts_context = ""
        if concepts_data:
            concepts = concepts_data.get("concepts", [])[:10]
            concepts_context = ", ".join(c.get("name", "") for c in concepts)

        prompt = f"""You are an expert interview coach preparing students for technical interviews and viva voce exams.

Based on this lecture content, generate a comprehensive set of interview and viva questions.

Key concepts covered: {concepts_context or "See transcript"}

Output ONLY valid JSON:
{{
    "technical_questions": [
        {{
            "question": "Explain the concept of X and its implementation",
            "expected_answer_points": ["Point 1", "Point 2"],
            "difficulty": "easy|medium|hard",
            "topic": "Related topic"
        }}
    ],
    "conceptual_questions": [
        {{
            "question": "Why does X happen when Y occurs?",
            "expected_answer_points": ["Point 1"],
            "difficulty": "medium",
            "topic": "Related topic"
        }}
    ],
    "scenario_questions": [
        {{
            "scenario": "Given that... what would you do?",
            "question": "How would you approach this?",
            "evaluation_criteria": ["Criterion 1"],
            "difficulty": "hard"
        }}
    ],
    "viva_questions": [
        {{
            "question": "Define X in your own words",
            "follow_up": "How does that relate to Y?",
            "topic": "Related topic"
        }}
    ],
    "difficulty_breakdown": {{"easy": 3, "medium": 5, "hard": 2}}
}}

Transcript:
{transcript_text[:6000]}"""

        try:
            from services.llm.model_selector import TaskType
            messages = [
                {"role": "system", "content": "You are an expert interview question generator. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ]
            response = await self.llm_manager.generate(TaskType.QUIZ_GENERATION, messages)
            raw = getattr(response, "text", None) or str(response)

            import re, json
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as exc:
            logger.error("InterviewService: generation failed: %s", exc)

        return {"technical_questions": [], "conceptual_questions": [], "viva_questions": []}

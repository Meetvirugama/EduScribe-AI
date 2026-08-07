"""
services/content/revision_service.py — Revision Sheet Generator

Generates condensed, exam-focused revision sheets from lecture content.
Unlike full notes, revision sheets prioritise density — key facts,
definitions, and formulas only, without explanatory prose.

Issue Resolved: #12 (notes generation not modular — missing revision generator)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RevisionService:
    """Generates condensed revision sheets for exam preparation."""

    def __init__(self, llm_manager=None) -> None:
        self.llm_manager = llm_manager

    async def generate_revision_sheet(
        self,
        transcript_segments: List[Dict[str, Any]],
        topics_data: Dict[str, Any] = None,
        concepts_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate a concise revision sheet.

        Returns:
            {
              "title": "Revision: Topic Name",
              "quick_facts": ["Fact 1", "Fact 2"],
              "key_definitions": [{"term": "...", "definition": "..."}],
              "important_formulas": ["F = ma", "E = mc²"],
              "must_know_points": ["Point 1", "Point 2"],
              "common_exam_topics": ["Topic 1", "Topic 2"],
              "last_minute_tips": ["Tip 1"]
            }
        """
        if not self.llm_manager:
            return {"quick_facts": [], "key_definitions": [], "must_know_points": []}

        transcript_text = " ".join(s.get("text", "") for s in transcript_segments)

        topics_context = ""
        if topics_data:
            topics = topics_data.get("topics", [])[:5]
            topics_context = ", ".join(t.get("title", "") for t in topics)

        concepts_context = ""
        if concepts_data:
            concepts = concepts_data.get("concepts", [])[:8]
            concepts_context = ", ".join(c.get("name", "") for c in concepts if c.get("importance") == "high")

        prompt = f"""You are an expert study coach. Create a concise, exam-focused revision sheet.

Focus on: facts, definitions, formulas, key points — NO lengthy explanations.

Topic areas: {topics_context or "See transcript"}
High-priority concepts: {concepts_context or "See transcript"}

Output ONLY valid JSON:
{{
    "title": "Revision Sheet: [Subject]",
    "quick_facts": ["Fact 1 — brief statement", "Fact 2"],
    "key_definitions": [
        {{"term": "Term", "definition": "Concise one-line definition"}}
    ],
    "important_formulas": ["Formula string or description"],
    "must_know_points": ["Critical point 1", "Critical point 2"],
    "common_exam_topics": ["Topic likely to appear in exam 1", "Topic 2"],
    "last_minute_tips": ["Memory trick or tip 1", "Tip 2"],
    "priority_topics": ["Must revise: Topic 1", "Should revise: Topic 2"]
}}

Transcript:
{transcript_text[:5000]}"""

        try:
            from services.llm.model_selector import TaskType
            messages = [
                {"role": "system", "content": "You are an exam revision expert. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ]
            response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)
            raw = getattr(response, "text", None) or str(response)

            import re, json
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as exc:
            logger.error("RevisionService: generation failed: %s", exc)

        return {"quick_facts": [], "key_definitions": [], "must_know_points": []}

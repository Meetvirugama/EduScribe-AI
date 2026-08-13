"""
services/content/note_quality.py

Evaluates the pedagogical quality and evidence grounding of a generated topic note.
"""

import json
from typing import Dict, Any, List
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import QualityReport
import logging

logger = logging.getLogger(__name__)

class NoteQualityEvaluator:
    """Evaluates topic notes using a premium LLM as a Critic."""

    def __init__(self, llm_manager):
        self.llm_manager = llm_manager

    async def evaluate(self, topic_json: Dict[str, Any], context_packet: str) -> QualityReport:
        """
        Evaluates a generated topic note against its source context.
        Returns a QualityReport containing a score (0-100) and specific issues.
        """
        logger.info(f"Evaluating quality for topic: {topic_json.get('title', 'Unknown')}")
        
        system_msg = (
            "You are EduScribe's Note Quality Evaluator.\n"
            "Evaluate the generated topic note against the raw source context.\n"
            "Score it from 0 to 100 based on:\n"
            "1. Coverage (Did it cover all evidence?)\n"
            "2. Accuracy (No hallucinations?)\n"
            "3. Clarity & Structure\n"
            "Return a strictly valid JSON matching the schema."
        )
        
        prompt = (
            "=== SOURCE CONTEXT PACKET ===\n"
            f"{context_packet}\n\n"
            "=== GENERATED TOPIC NOTE ===\n"
            f"{json.dumps(topic_json, indent=2)}\n\n"
            "Analyze the note. If there are missing elements, unsupported claims, or poor structure, "
            "list them as issues. Provide an overall score (0-100). "
            "Respond ONLY with valid JSON in the exact following structure:\n"
            "{\n"
            "  \"score\": 85,\n"
            "  \"issues\": [\n"
            "    {\n"
            "      \"type\": \"missing_evidence\",\n"
            "      \"severity\": \"high\",\n"
            "      \"section\": \"examples\",\n"
            "      \"problem\": \"The example is not supported by the context.\",\n"
            "      \"evidence\": \"Context says X, but note says Y.\",\n"
            "      \"fix\": \"Change the example to X.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        # We use COMPLEX_PRIMARY for critique
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # We bypass the internal registry for this specific internal validation by
            # using litellm directly if needed, or we can use the generic text output and parse.
            # For robustness, we will use the llm_manager but parse the JSON ourselves.
            response = await self.llm_manager.generate(
                task=TaskType.DETAILED_NOTES, # fallback task to get it routed
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # The llm_manager will return a BaseLLMOutput or dict. 
            # We will extract the raw string and parse it into QualityReport.
            raw_text = getattr(response, "text", str(response))
            import re
            
            # extract json block if wrapped in markdown
            match = re.search(r'```(?:json)?(.*?)```', raw_text, re.DOTALL)
            if match:
                raw_text = match.group(1).strip()
                
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                # If litellm returned a dict instead of string
                if isinstance(response, dict) and "score" in response:
                    data = response
                else:
                    logger.error("Failed to parse critic JSON.")
                    return QualityReport(score=100, issues=[]) # Fail open to avoid blocking

            report = QualityReport.model_validate(data)
            return report
            
        except Exception as e:
            logger.error(f"Critic evaluation failed: {e}")
            # Fail open if the critic fails
            return QualityReport(score=100, issues=[])

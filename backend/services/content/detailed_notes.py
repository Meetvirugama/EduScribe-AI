import logging
import json
import asyncio
from typing import Dict, Any, List

from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from .note_quality import NoteQualityEvaluator
from .markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)

class DetailedNotesGenerator(BaseContentService):
    async def generate_detailed_notes(self, context: LectureContext) -> Dict[str, Any]:
        """Generates detailed, structured notes using a multi-step compiler pipeline."""
        logger.info("Generating detailed notes artifact via compiler pipeline...")
        
        empty_result = {"notes_markdown": "Failed to generate notes."}
        
        if not self.llm_manager:
            return empty_result
            
        if not context.topics:
            logger.warning("No topics available for detailed notes generation.")
            return empty_result

        evaluator = NoteQualityEvaluator(self.llm_manager)
        topic_markdowns = []

        # Process each topic concurrently or sequentially.
        # We will do it sequentially to preserve strict ordering and avoid rate limits.
        for index, topic in enumerate(context.topics):
            topic_title = getattr(topic, "title", f"Topic {index+1}")
            logger.info(f"Processing Topic: {topic_title}")

            # 1. Context Packet Builder
            context_packet = self._build_context_packet(topic_title, context)

            # 2. LLM Topic Synthesis
            topic_json = await self._synthesize_topic(topic_title, context_packet)

            if not topic_json:
                continue

            # 3. Topic Validation (Critic)
            quality_report = await evaluator.evaluate(topic_json, context_packet)

            # 4. Targeted Repair (if score < 85)
            if quality_report.score < 85 and quality_report.issues:
                logger.info(f"Repairing topic {topic_title} (Score: {quality_report.score})")
                topic_json = await self._repair_topic(topic_json, quality_report.issues, context_packet)

            # 5. Render to Markdown
            t_md = MarkdownRenderer.render_topic(topic_json)
            topic_markdowns.append(t_md)

        # 6. Final Assembly
        final_markdown = MarkdownRenderer.compile_final_notes(
            lecture_title=context.metadata.get("title", "Lecture Notes"),
            topic_markdowns=topic_markdowns
        )
        context.detailed_notes_md = final_markdown

        return {"notes_markdown": final_markdown}

    def _build_context_packet(self, topic_title: str, context: LectureContext) -> str:
        """Assembles a highly specific context packet for a single topic."""
        packet = []
        packet.append(f"TOPIC: {topic_title}")
        packet.append(f"TRANSCRIPT:\n{context.transcript}")

        # In a fully fleshed out system, we would filter these by topic_association.
        # For now, we provide the global context and ask the LLM to pull what's relevant to this topic.
        if context.concepts:
            packet.append("CONCEPTS:")
            for c in context.concepts:
                packet.append(f"- {getattr(c, 'name', '')}: {getattr(c, 'brief_description', '')}")
                
        if context.definitions:
            packet.append("DEFINITIONS:")
            for d in context.definitions:
                packet.append(f"- {getattr(d, 'term', '')}: {getattr(d, 'definition', '')}")
                
        if context.examples:
            packet.append("EXAMPLES:")
            for e in context.examples:
                packet.append(f"- {getattr(e, 'title', '')}: {getattr(e, 'problem', '')}")

        if context.key_points:
            packet.append("KEY POINTS:")
            for k in context.key_points:
                packet.append(f"- {getattr(k, 'text', '')}")

        return "\n\n".join(packet)

    async def _synthesize_topic(self, topic_title: str, context_packet: str) -> Dict[str, Any]:
        """Generates the structured JSON note for a topic."""
        system_msg = (
            "You are an expert technical educator.\n"
            "Generate a highly structured educational note for the specific TOPIC using ONLY the provided CONTEXT PACKET.\n"
            "Format the output strictly as a JSON object with the following keys:\n"
            "{\n"
            '  "title": "Topic Name",\n'
            '  "overview": "Brief summary",\n'
            '  "core_idea": "Main concept",\n'
            '  "steps": ["Step 1", "Step 2"],\n'
            '  "important_terms": [{"term": "T", "meaning": "M"}],\n'
            '  "formulas": [{"expression": "E", "explanation": "E"}],\n'
            '  "examples": [{"problem": "P", "solution": "S"}],\n'
            '  "relationships": ["Rel 1"],\n'
            '  "misconceptions": ["Misc 1"],\n'
            '  "key_takeaways": ["Takeaway 1"]\n'
            "}\n"
            "Omit keys or use empty lists if the context does not support them. Do not hallucinate."
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": context_packet}
        ]

        try:
            # Bypass registry for strict internal JSON loop by using response_format
            response = await self.llm_manager.generate(
                task=TaskType.DETAILED_NOTES,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            raw_text = getattr(response, "text", str(response))
            import re
            match = re.search(r'```(?:json)?(.*?)```', raw_text, re.DOTALL)
            if match:
                raw_text = match.group(1).strip()
            
            return json.loads(raw_text)
            
        except Exception as e:
            logger.error(f"Failed to synthesize topic {topic_title}: {e}")
            return {}

    async def _repair_topic(self, topic_json: Dict[str, Any], issues: List[Any], context_packet: str) -> Dict[str, Any]:
        """Repairs a topic note based on critic feedback."""
        system_msg = (
            "You are an expert Note Repair editor.\n"
            "Fix the provided topic JSON based on the critic issues. Return ONLY the repaired JSON."
        )
        
        issues_text = "\\n".join([f"- [{i.severity}] {i.type} in {i.section}: {i.problem} -> Fix: {i.fix}" for i in issues])
        
        prompt = (
            f"=== CONTEXT ===\n{context_packet}\n\n"
            f"=== ISSUES TO FIX ===\n{issues_text}\n\n"
            f"=== CURRENT JSON ===\n{json.dumps(topic_json, indent=2)}\n\n"
            "Return the corrected JSON."
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm_manager.generate(
                task=TaskType.DETAILED_NOTES,
                messages=messages,
                response_format={"type": "json_object"}
            )
            raw_text = getattr(response, "text", str(response))
            import re
            match = re.search(r'```(?:json)?(.*?)```', raw_text, re.DOTALL)
            if match:
                raw_text = match.group(1).strip()
            return json.loads(raw_text)
            
        except Exception as e:
            logger.error(f"Failed to repair topic: {e}")
            return topic_json # Return original if repair fails

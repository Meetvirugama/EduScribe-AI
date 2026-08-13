import logging
import json
from typing import Dict, Any, List

from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from .note_quality import NoteQualityEvaluator
from .markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)


class DetailedNotesGenerator(BaseContentService):
    async def generate_detailed_notes(
            self, context: LectureContext) -> Dict[str, Any]:
        """Generates detailed, structured notes using a multi-step compiler pipeline."""
        logger.info(
            "Generating detailed notes artifact via compiler pipeline...")

        empty_result = {"notes_markdown": "Failed to generate notes."}

        if not self.llm_manager:
            return empty_result

        if not context.topics:
            logger.warning(
                "No topics available for detailed notes generation.")
            return empty_result

        evaluator = NoteQualityEvaluator(self.llm_manager)
        topic_markdowns = []

        # Process each topic concurrently or sequentially.
        # We will do it sequentially to preserve strict ordering and avoid rate
        # limits.
        for index, topic in enumerate(context.topics):
            topic_title = getattr(topic, "title", f"Topic {index+1}")
            logger.info(f"Processing Topic: {topic_title}")

            # 2. LLM Topic Synthesis
            topic_json = await self._synthesize_topic(topic, context)

            if not topic_json or not topic_json.get("notes_markdown"):
                continue

            # 3. Topic Validation (Critic)
            quality_report = await evaluator.evaluate(topic_json, "")

            # 4. Targeted Repair (if score < 85)
            if quality_report.score < 85 and quality_report.issues:
                logger.info(
                    f"Repairing topic {topic_title} (Score: {quality_report.score})")
                topic_json = await self._repair_topic(topic_json, quality_report.issues, topic_title)

            # 5. Render to Markdown
            t_md = MarkdownRenderer.render_topic(topic_json)
            if t_md:
                topic_markdowns.append(t_md)

        # 6. Final Assembly
        final_markdown = MarkdownRenderer.compile_final_notes(
            lecture_title=context.metadata.get("title", "Lecture Notes"),
            topic_markdowns=topic_markdowns
        )
        context.detailed_notes_md = final_markdown

        return {"notes_markdown": final_markdown}

    def _hhmmss_to_sec(self, time_str: str) -> float:
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except Exception:
            pass
        return 0.0

    def _build_context_packet(self, topic: Any,
                              context: LectureContext) -> tuple[str, str]:
        """Returns (enriched_chunk, cross_chunk_context)"""
        topic_title = getattr(topic, "title", "Topic")
        
        enriched = []
        enriched.append(f"Title: {topic_title}")
        
        # 1. Inject Raw Transcript & OCR using start/end times
        start_time_str = getattr(topic, "start_time", "00:00:00")
        end_time_str = getattr(topic, "end_time", "00:00:00")
        
        start_sec = self._hhmmss_to_sec(start_time_str)
        end_sec = self._hhmmss_to_sec(end_time_str)
        
        # If timestamps are valid, extract the exact segment window
        if end_sec > start_sec:
            raw_text = []
            
            # Transcript text
            if context.segments:
                segment_texts = [s.get("text", "") for s in context.segments 
                               if start_sec <= float(s.get("start", 0.0)) <= end_sec]
                if segment_texts:
                    raw_text.append("### Source Transcript")
                    raw_text.append(" ".join(segment_texts))
            
            # OCR text
            if context.frames:
                frame_texts = []
                sorted_frames = sorted(context.frames, key=lambda f: f.get("time_sec", 0.0))
                for f in sorted_frames:
                    t = f.get("time_sec", 0.0)
                    ocr = f.get("ocr", "").strip()
                    if start_sec <= t <= end_sec and ocr:
                        scene = f.get("scene_number", "?")
                        frame_texts.append(f"**[Timestamp: {round(t, 1)}s | Scene {scene}]**\n> {ocr}")
                
                if frame_texts:
                    raw_text.append("\n### Source Visual Content (OCR)")
                    raw_text.extend(frame_texts)
            
            if raw_text:
                enriched.append("\n".join(raw_text))
        
        # 2. Inject Key Takeaways
        takeaways = getattr(topic, "key_takeaways", [])
        if takeaways:
            enriched.append("\nKey Takeaways:")
            for t in takeaways:
                enriched.append(f"- {t}")
                
        global_ctx = []
        if context.concepts:
            global_ctx.append("CONCEPTS:")
            for c in context.concepts:
                global_ctx.append(f"- {getattr(c, 'name', '')}: {getattr(c, 'brief_description', '')}")

        if context.definitions:
            global_ctx.append("DEFINITIONS:")
            for d in context.definitions:
                global_ctx.append(f"- {getattr(d, 'term', '')}: {getattr(d, 'definition', '')}")

        if context.examples:
            global_ctx.append("EXAMPLES:")
            for e in context.examples:
                global_ctx.append(f"- {getattr(e, 'title', '')}: {getattr(e, 'problem', '')}")

        if context.key_points:
            global_ctx.append("KEY POINTS:")
            for k in context.key_points:
                global_ctx.append(f"- {getattr(k, 'text', '')}")

        return "\n\n".join(enriched), "\n\n".join(global_ctx)

    async def _synthesize_topic(
            self, topic: Any, context: LectureContext) -> Dict[str, Any]:
        """Generates the structured JSON note for a topic."""
        topic_title = getattr(topic, "title", "Topic")
        enriched_chunk, cross_chunk_context = self._build_context_packet(topic, context)
        from .prompts import PromptManager
        
        try:
            system_msg = PromptManager.render(
                "detailed_notes_artifact",
                chunk_label=topic_title,
                enriched_chunk=enriched_chunk,
                cross_chunk_context=cross_chunk_context
            )
        except Exception as e:
            logger.error(f"Could not render detailed_notes_artifact.md: {e}")
            return {}

        messages = [
            {"role": "system", "content": system_msg}
        ]

        try:
            response = await self.llm_manager.generate(
                task=TaskType.TOPIC_NOTE_WRITING,
                messages=messages,
                response_format={"type": "json_object"}
            )
            if hasattr(response, "model_dump"):
                return response.model_dump()
            return {"notes_markdown": getattr(response, "text", "")}

        except Exception as e:
            logger.error(f"Failed to synthesize topic {topic_title}: {e}")
            return {}

    async def _repair_topic(
            self, topic_json: Dict[str, Any], issues: List[Any], topic_title: str) -> Dict[str, Any]:
        """Repairs a topic note based on critic feedback."""
        system_msg = (
            "You are an expert Note Repair editor.\n"
            "Fix the provided topic JSON based on the critic issues. Return ONLY the repaired JSON."
        )

        issues_text = "\\n".join(
            [f"- [{i.severity}] {i.type} in {i.section}: {i.problem} -> Fix: {i.fix}" for i in issues])

        prompt = (
            f"=== TOPIC TITLE ===\n{topic_title}\n\n"
            f"=== ISSUES TO FIX ===\n{issues_text}\n\n"
            f"=== CURRENT JSON ===\n{json.dumps(topic_json, indent=2)}\n\n"
            "Return the corrected JSON matching the exact schema."
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm_manager.generate(
                task=TaskType.NOTE_REPAIR,
                messages=messages,
                response_format={"type": "json_object"}
            )
            if hasattr(response, "model_dump"):
                return response.model_dump()
            return {"notes_markdown": getattr(response, "text", "")}

        except Exception as e:
            logger.error(f"Failed to repair topic: {e}")
            return topic_json

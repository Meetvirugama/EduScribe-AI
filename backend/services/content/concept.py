from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from ..llm.validation.schemas.notes import ConceptsOutput
from schemas.content import Concept, SourceReference

logger = logging.getLogger(__name__)


class ConceptService(BaseContentService):
    async def extract_concepts(
            self, context: LectureContext) -> Dict[str, Any]:
        """Extracts key academic concepts, technical terms, and important keywords."""
        logger.info("Extracting concepts and keywords...")

        import time
        start_time = time.time()
        # Inline chunking logic (fallback)
        video_id = context.metadata.get("video_id", "default_video")

        if not context.segments:
            chunks = []
        else:
            chunks = self._chunk_segments_with_ocr(context, video_id, use_semantic_chunking=False)

        chunks_context = "\n".join([
            f"[{c['chunk_id']} | {c['start_time']} - {c['end_time']}] {c['text']}"
            for c in chunks
        ])

        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="concept_extraction",
            chunks_context=chunks_context
        )

        try:
            response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)

            # The LLMManager should return ConceptsOutput (parsed schema)

            if isinstance(response, ConceptsOutput):
                parsed = response
            else:
                # Fallback to _safe_dump and manual parse if needed
                result = self._safe_dump(
                    response,
                    fallback={
                        "concepts": [],
                        "keywords": [],
                        "key_phrases": []})
                parsed = ConceptsOutput(**result)

            # Create a lookup dictionary for chunks
            chunk_lookup = {c['chunk_id']: c for c in chunks}

            # Map validation schema to domain models
            domain_concepts = []
            for c_item in parsed.concepts:
                sources = []
                for src in c_item.sources:
                    # Look up exact timestamps from the original chunks if
                    # valid
                    original_chunk = chunk_lookup.get(src.chunk_id)
                    t_start = original_chunk['start_time'] if original_chunk else src.timestamp_start
                    t_end = original_chunk['end_time'] if original_chunk else src.timestamp_end

                    sources.append(
                        SourceReference(
                            chunk_id=src.chunk_id,
                            timestamp_start=t_start,
                            timestamp_end=t_end
                        )
                    )
                domain_concepts.append(Concept(
                    name=c_item.name,
                    category=c_item.category,
                    importance=c_item.importance,
                    brief_description=c_item.brief_description,
                    source=sources
                ))

            # Save to context for reuse by downstream services
            context.concepts = domain_concepts

            execution_time = round(time.time() - start_time, 2)

            return {
                "status": "success",
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": {
                    "concepts": [c.model_dump(exclude_none=True) for c in domain_concepts],
                    "keywords": parsed.keywords,
                    "key_phrases": parsed.key_phrases
                }
            }

        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            execution_time = round(time.time() - start_time, 2)

            # Keep existing concepts if failure occurs
            return {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": {
                    "concepts": [c.model_dump(exclude_none=True) for c in context.concepts] if context.concepts else [],
                    "keywords": [],
                    "key_phrases": []
                }
            }

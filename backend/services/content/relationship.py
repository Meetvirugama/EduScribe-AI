import time
from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import Relationship
from ..llm.validation.schemas.notes import RelationshipsOutput

logger = logging.getLogger(__name__)


class RelationshipService(BaseContentService):
    async def extract_relationships(
            self, context: LectureContext) -> Dict[str, Any]:
        """Extracts relationships between concepts from the lecture content in chunks to avoid token limits."""
        logger.info("Extracting concept relationships...")
        start_time = time.time()

        video_id = context.metadata.get("video_id", "default_video")

        if not context.segments:
            chunks = []
        else:
            chunks = self._chunk_segments_with_ocr(context, video_id, use_semantic_chunking=False)

        # Build concepts context to guide relationship extraction
        concepts = context.concepts[:20] if context.concepts else []
        concepts_context = ", ".join(
            getattr(c, "name", str(c)) for c in concepts)

        try:
            all_relationships = []

            final_provider = "unknown"
            final_model = "unknown"
            total_latency = 0.0
            total_tokens = 0

            for c in chunks:
                chunk_id = c["chunk_id"]
                chunks_context = f'[{chunk_id} | {c["start_time"]} - {c["end_time"]}]\n{c["text"]}'

                messages = self._render_messages(
                    system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
                    template_name="relationship_extraction",
                    chunks_context=chunks_context,
                    concepts_context=concepts_context or "See transcript"
                )

                try:
                    import asyncio
                    await asyncio.sleep(0.5)

                    response = await self.llm_manager.generate(TaskType.RELATIONSHIP_EXTRACTION, messages)

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
                        response, fallback={"relationships": []})
                    parsed = RelationshipsOutput(**raw_dict)

                    for r_item in parsed.relationships:
                        all_relationships.append(r_item)

                except Exception as inner_exc:
                    logger.warning(
                        f"Failed to extract relationships for chunk {chunk_id}: {inner_exc}")

            final_parsed = RelationshipsOutput(
                relationships=all_relationships,
                provider=final_provider,
                model=final_model,
                latency=round(total_latency, 2),
                total_tokens=total_tokens
            )

            # Convert to domain objects
            domain_relationships = []
            for r in final_parsed.relationships:
                domain_relationships.append(Relationship(
                    from_concept=r.from_concept,
                    relationship_type=r.relationship_type,
                    to_concept=r.to_concept
                ))

            context.relationships = domain_relationships

            execution_time = round(time.time() - start_time, 2)
            return {
                "status": "success",
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": final_parsed.model_dump(exclude_none=True)
            }

        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            return {"relationships": context.relationships}

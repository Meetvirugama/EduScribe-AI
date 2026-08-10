from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import Relationship

logger = logging.getLogger(__name__)

class RelationshipService(BaseContentService):
    async def extract_relationships(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts relationships between concepts from the lecture content."""
        logger.info("Extracting concept relationships...")
        
        from ..rag.chunker import ChunkerFactory, ChunkStrategy
        chunker = ChunkerFactory.get(ChunkStrategy.TIMESTAMP.value)
        video_id = context.metadata.get("video_id", "default_video")
        
        if not context.segments:
            chunks = chunker.chunk([{"text": context.transcript}], video_id=video_id)
        else:
            chunks = chunker.chunk(context.segments, video_id=video_id)
             
        chunks_context = "\n\n".join([
            f'<chunk id="{c.chunk_id}" start="{c.start_time}" end="{c.end_time}">\n{c.text}\n</chunk>'
            for c in chunks
        ])
        
        # Build concepts context to guide relationship extraction
        concepts = context.concepts[:20] if context.concepts else []
        concepts_context = ", ".join(getattr(c, "name", str(c)) for c in concepts)
        
        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="relationship_extraction",
            chunks_context=chunks_context,
            concepts_context=concepts_context or "See transcript"
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)
            
            result = self._safe_dump(response, fallback={"relationships": []})
            
            domain_relationships = []
            for r in result.get("relationships", []):
                domain_relationships.append(Relationship(
                    from_concept=r.get("from_concept", ""),
                    relationship_type=r.get("relationship_type", ""),
                    to_concept=r.get("to_concept", "")
                ))
            
            context.relationships = domain_relationships
            
            return {"relationships": domain_relationships}
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            return {"relationships": context.relationships}

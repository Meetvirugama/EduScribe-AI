from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import Concept, SourceReference

logger = logging.getLogger(__name__)

class ConceptService(BaseContentService):
    async def extract_concepts(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts key academic concepts, technical terms, and important keywords."""
        logger.info("Extracting concepts and keywords...")
        # Chunk-aware processing
        from ..rag.chunker import ChunkerFactory, ChunkStrategy
        chunker = ChunkerFactory.get(ChunkStrategy.TIMESTAMP.value)
        video_id = context.metadata.get("video_id", "default_video")
        
        # If segments aren't passed, fallback to basic chunking of transcript
        if not context.segments:
             chunks = chunker.chunk([{"text": context.transcript}], video_id=video_id)
        else:
             chunks = chunker.chunk(context.segments, video_id=video_id)
             
        chunks_context = "\n\n".join([
            f"<chunk id=\"{c.chunk_id}\" start=\"{c.start_time}\" end=\"{c.end_time}\">\n{c.text}\n</chunk>"
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
            from ..llm.validation.schemas.notes import ConceptsOutput
            
            if isinstance(response, ConceptsOutput):
                parsed = response
            else:
                # Fallback to _safe_dump and manual parse if needed
                result = self._safe_dump(response, fallback={"concepts": [], "keywords": [], "key_phrases": []})
                parsed = ConceptsOutput(**result)
            
            # Map validation schema to domain models
            domain_concepts = []
            for c_item in parsed.concepts:
                sources = [
                    SourceReference(
                        chunk_id=src.chunk_id,
                        timestamp_start=src.timestamp_start,
                        timestamp_end=src.timestamp_end
                    ) for src in c_item.sources
                ]
                domain_concepts.append(Concept(
                    name=c_item.name,
                    category=c_item.category,
                    importance=c_item.importance,
                    brief_description=c_item.brief_description,
                    source=sources
                ))
            
            # Save to context for reuse by downstream services
            context.concepts = domain_concepts
            
            return {
                "concepts": domain_concepts,
                "keywords": parsed.keywords,
                "key_phrases": parsed.key_phrases
            }
            
        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            # Keep existing concepts if failure occurs
            return {
                "concepts": context.concepts, 
                "keywords": [], 
                "key_phrases": []
            }

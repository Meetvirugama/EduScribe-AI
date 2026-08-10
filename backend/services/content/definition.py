from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import Definition, SourceReference

logger = logging.getLogger(__name__)

class DefinitionService(BaseContentService):
    async def extract_definitions(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts formal definitions from the lecture content."""
        logger.info("Extracting definitions...")
        
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
        
        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="definition_extraction",
            chunks_context=chunks_context
        )
        
        try:
            # Reusing CONCEPT_EXTRACTION task type as it fits the extraction profile
            response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)
            
            result = self._safe_dump(response, fallback={"definitions": []})
            
            domain_definitions = []
            for d in result.get("definitions", []):
                sources = []
                for src in d.get("sources", []):
                    sources.append(SourceReference(
                        chunk_id=src.get("chunk_id", ""),
                        timestamp_start=src.get("timestamp_start"),
                        timestamp_end=src.get("timestamp_end")
                    ))
                
                domain_definitions.append(Definition(
                    term=d.get("term", ""),
                    definition=d.get("definition", ""),
                    source=sources
                ))
            
            context.definitions = domain_definitions
            
            return {"definitions": domain_definitions}
            
        except Exception as e:
            logger.error(f"Definition extraction failed: {e}")
            return {"definitions": context.definitions}

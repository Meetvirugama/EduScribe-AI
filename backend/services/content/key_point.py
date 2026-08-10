from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import KeyPoint, SourceReference

logger = logging.getLogger(__name__)

class KeyPointService(BaseContentService):
    async def extract_key_points(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts key points from the lecture content."""
        logger.info("Extracting key points...")
        
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
            template_name="key_point_extraction",
            chunks_context=chunks_context
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)
            
            result = self._safe_dump(response, fallback={"key_points": []})
            
            domain_key_points = []
            for k in result.get("key_points", []):
                sources = []
                for src in k.get("sources", []):
                    sources.append(SourceReference(
                        chunk_id=src.get("chunk_id", ""),
                        timestamp_start=src.get("timestamp_start"),
                        timestamp_end=src.get("timestamp_end")
                    ))
                
                domain_key_points.append(KeyPoint(
                    text=k.get("text", ""),
                    importance=k.get("importance"),
                    category=k.get("category"),
                    topic=k.get("topic"),
                    timestamp=k.get("timestamp"),
                    source=sources
                ))
            
            context.key_points = domain_key_points
            
            return {"key_points": domain_key_points}
            
        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return {"key_points": context.key_points}

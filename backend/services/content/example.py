from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import Example, SourceReference

logger = logging.getLogger(__name__)

class ExampleService(BaseContentService):
    async def extract_examples(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts examples from the lecture content."""
        logger.info("Extracting examples...")
        
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
            template_name="example_extraction",
            chunks_context=chunks_context
        )
        
        try:
            response = await self.llm_manager.generate(TaskType.CONCEPT_EXTRACTION, messages)
            
            result = self._safe_dump(response, fallback={"examples": []})
            
            domain_examples = []
            for e in result.get("examples", []):
                sources = []
                for src in e.get("sources", []):
                    sources.append(SourceReference(
                        chunk_id=src.get("chunk_id", ""),
                        timestamp_start=src.get("timestamp_start"),
                        timestamp_end=src.get("timestamp_end")
                    ))
                
                domain_examples.append(Example(
                    title=e.get("title", ""),
                    problem=e.get("problem", ""),
                    explanation=e.get("explanation"),
                    solution=e.get("solution"),
                    topic=e.get("topic"),
                    timestamp=e.get("timestamp"),
                    source=sources
                ))
            
            context.examples = domain_examples
            
            return {"examples": domain_examples}
            
        except Exception as e:
            logger.error(f"Example extraction failed: {e}")
            return {"examples": context.examples}

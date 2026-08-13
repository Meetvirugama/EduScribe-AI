from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import Example, SourceReference

logger = logging.getLogger(__name__)


class ExampleService(BaseContentService):
    async def extract_examples(
            self, context: LectureContext) -> Dict[str, Any]:
        """Extracts examples from the lecture content."""
        logger.info("Extracting examples...")

        import time
        start_time = time.time()
        video_id = context.metadata.get("video_id", "default_video")

        chunks = []
        if not context.segments:
            chunks.append({
                "chunk_id": f"{video_id}_0",
                "start_time": 0.0,
                "end_time": 0.0,
                "text": context.transcript
            })
        else:
            current_text = []
            current_start = None
            current_end = 0.0
            chunk_index = 0

            for seg in context.segments:
                seg_start = seg.get("start", 0.0)
                if current_start is None:
                    current_start = seg_start

                current_text.append(seg.get("text", ""))

                if "end" in seg:
                    current_end = seg["end"]
                elif "duration" in seg:
                    current_end = seg_start + seg.get("duration", 0.0)
                else:
                    current_end = seg_start

                # Group into timestamp ranges (approx 3 mins or 2000 chars)
                if current_end - \
                        current_start >= 180.0 or sum(len(t) for t in current_text) > 2000:
                    chunks.append({
                        "chunk_id": f"{video_id}_range_{chunk_index}",
                        "start_time": round(current_start, 2),
                        "end_time": round(current_end, 2),
                        "text": " ".join(current_text)
                    })
                    chunk_index += 1
                    current_text = []
                    current_start = None

            if current_text:
                chunks.append({
                    "chunk_id": f"{video_id}_range_{chunk_index}",
                    "start_time": round(current_start, 2) if current_start is not None else 0.0,
                    "end_time": round(current_end, 2),
                    "text": " ".join(current_text)
                })

        chunks_context = "\n".join([
            f"[{c['chunk_id']} | {c['start_time']} - {c['end_time']}] {c['text']}"
            for c in chunks
        ])

        messages = self._render_messages(
            system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
            template_name="example_extraction",
            chunks_context=chunks_context
        )

        try:
            response = await self.llm_manager.generate(TaskType.EXAMPLE_EXTRACTION, messages)

            result = self._safe_dump(response, fallback={"examples": []})

            chunk_lookup = {c['chunk_id']: c for c in chunks}

            domain_examples = []
            for e in result.get("examples", []):
                sources = []
                for src in e.get("sources", []):
                    chunk_id = src.get("chunk_id", "")
                    original_chunk = chunk_lookup.get(chunk_id)
                    t_start = original_chunk['start_time'] if original_chunk else src.get(
                        "timestamp_start")
                    t_end = original_chunk['end_time'] if original_chunk else src.get(
                        "timestamp_end")

                    sources.append(SourceReference(
                        chunk_id=chunk_id,
                        timestamp_start=t_start,
                        timestamp_end=t_end
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

            execution_time = round(time.time() - start_time, 2)

            return {
                "status": "success",
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": {
                    "examples": [e.model_dump(exclude_none=True) for e in domain_examples]
                }
            }

        except Exception as e:
            logger.error(f"Example extraction failed: {e}")
            execution_time = round(time.time() - start_time, 2)

            return {
                "status": "error",
                "error": str(e),
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks) if 'chunks' in locals() else 0
                },
                "data": {
                    "examples": [e.model_dump(exclude_none=True) for e in context.examples] if context.examples else []
                }
            }

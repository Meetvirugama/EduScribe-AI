import time
import logging
from typing import Any, Dict
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from ..llm.validation.schemas.notes import TopicsAndNotesOutput

logger = logging.getLogger(__name__)

class TopicService(BaseContentService):
    def _chunk_segments(self, segments: list, video_id: str) -> list:
        chunks = []
        if not segments:
            return chunks
            
        current_text = []
        current_start = None
        current_end = 0.0
        chunk_index = 0
        
        for seg in segments:
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
            if current_end - current_start >= 180.0 or sum(len(t) for t in current_text) > 2000:
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
            
        return chunks

    async def extract_topics(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts detailed notes and topics from the transcript using chunks."""
        logger.info("Extracting topics...")
        start_time = time.time()
        
        empty_result = {"summary": "Failed to extract topics.", "topics": []}
        
        if not self.llm_manager:
            return empty_result
            
        video_id = context.metadata.get("video_id", "default_video")
        
        if not context.segments:
            chunks = self._chunk_segments([{"text": context.transcript}], video_id)
        else:
            chunks = self._chunk_segments(context.segments, video_id)
            
        try:
            all_topics = []
            summaries = []
            
            final_provider = "unknown"
            final_model = "unknown"
            total_latency = 0.0
            total_tokens = 0
            
            for c in chunks:
                chunk_id = c["chunk_id"]
                transcript_text = f'[{chunk_id} | {c["start_time"]} - {c["end_time"]}]\n{c["text"]}'
                
                messages = self._render_messages(
                    system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
                    template_name="topic_extraction",
                    transcript_text=transcript_text
                )
                
                try:
                    import asyncio
                    await asyncio.sleep(0.5)
                    
                    response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)
                    
                    if hasattr(response, "provider") and response.provider != "unknown":
                        final_provider = response.provider
                    if hasattr(response, "model") and response.model != "unknown":
                        final_model = response.model
                    if hasattr(response, "latency"):
                        total_latency += response.latency
                    if hasattr(response, "total_tokens"):
                        total_tokens += response.total_tokens
                        
                    raw_dict = self._safe_dump(response, fallback=empty_result)
                    parsed = TopicsAndNotesOutput(**raw_dict)
                    
                    if parsed.summary:
                        summaries.append(parsed.summary)
                    
                    for t_item in parsed.topics:
                        all_topics.append(t_item)
                        
                except Exception as inner_exc:
                    logger.warning(f"Failed to extract topics for chunk {chunk_id}: {inner_exc}")
            
            combined_summary = "\n\n".join(summaries) if summaries else "No summary generated."
            
            final_parsed = TopicsAndNotesOutput(
                summary=combined_summary,
                topics=all_topics,
                provider=final_provider,
                model=final_model,
                latency=round(total_latency, 2),
                total_tokens=total_tokens
            )
            
            # Save parsed topics back to context so downstream services can use them
            context.topics = [t.model_dump() for t in final_parsed.topics]
            
            execution_time = round(time.time() - start_time, 2)
            
            result_dict = final_parsed.model_dump(exclude_none=True)
            
            return {
                "status": "success",
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": result_dict
            }
            
        except Exception as exc:
            logger.error("TopicService: extraction failed: %s", exc)
            return empty_result

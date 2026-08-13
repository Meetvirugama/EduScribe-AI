import time
from typing import Dict, Any
import logging
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from schemas.content import KeyPoint, SourceReference
from ..llm.validation.schemas.notes import KeyPointsOutput, SourceReferenceItem

logger = logging.getLogger(__name__)

class KeyPointService(BaseContentService):
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

    async def extract_key_points(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts key points from the lecture content in chunks to avoid token limits."""
        logger.info("Extracting key points...")
        start_time = time.time()
        
        video_id = context.metadata.get("video_id", "default_video")
        
        if not context.segments:
            chunks = self._chunk_segments([{"text": context.transcript}], video_id)
        else:
            chunks = self._chunk_segments(context.segments, video_id)
             
        try:
            all_key_points = []
            
            final_provider = "unknown"
            final_model = "unknown"
            total_latency = 0.0
            total_tokens = 0
            
            for c in chunks:
                chunk_id = c["chunk_id"]
                chunks_context = f'[{chunk_id} | {c["start_time"]} - {c["end_time"]}]\n{c["text"]}'
                
                messages = self._render_messages(
                    system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
                    template_name="key_point_extraction",
                    chunks_context=chunks_context
                )
                
                try:
                    import asyncio
                    await asyncio.sleep(0.5)
                    
                    response = await self.llm_manager.generate(TaskType.KEY_POINTS_EXTRACTION, messages)
                    
                    if hasattr(response, "provider") and response.provider != "unknown":
                        final_provider = response.provider
                    if hasattr(response, "model") and response.model != "unknown":
                        final_model = response.model
                    if hasattr(response, "latency"):
                        total_latency += response.latency
                    if hasattr(response, "total_tokens"):
                        total_tokens += response.total_tokens
                        
                    raw_dict = self._safe_dump(response, fallback={"key_points": []})
                    parsed = KeyPointsOutput(**raw_dict)
                    
                    for k_item in parsed.key_points:
                        if not k_item.sources:
                            k_item.sources = [SourceReferenceItem(
                                chunk_id=chunk_id,
                                timestamp_start=c['start_time'],
                                timestamp_end=c['end_time']
                            )]
                        else:
                            for src in k_item.sources:
                                src.timestamp_start = c['start_time']
                                src.timestamp_end = c['end_time']
                        all_key_points.append(k_item)
                        
                except Exception as inner_exc:
                    logger.warning(f"Failed to extract key points for chunk {chunk_id}: {inner_exc}")
            
            final_parsed = KeyPointsOutput(
                key_points=all_key_points,
                provider=final_provider,
                model=final_model,
                latency=round(total_latency, 2),
                total_tokens=total_tokens
            )
            
            # Convert to domain objects
            domain_key_points = []
            for k in final_parsed.key_points:
                sources = []
                for src in k.sources:
                    sources.append(SourceReference(
                        chunk_id=src.chunk_id,
                        timestamp_start=src.timestamp_start,
                        timestamp_end=src.timestamp_end
                    ))
                
                domain_key_points.append(KeyPoint(
                    text=k.text,
                    importance=k.importance,
                    category=k.category,
                    topic=k.topic,
                    timestamp=sources[0].timestamp_start if sources else None,
                    source=sources
                ))
            
            context.key_points = domain_key_points
            
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
            logger.error(f"Key point extraction failed: {e}")
            return {"key_points": context.key_points}

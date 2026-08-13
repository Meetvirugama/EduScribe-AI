import logging
from typing import Any, Dict, List
from .context import LectureContext
from ..llm.llm_manager import LLMManager
from .prompts import PromptManager
from ..llm.validation.schemas.core import GenericTextOutput

logger = logging.getLogger(__name__)


class BaseContentService:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager

    def _render_messages(self, system_msg: str,
                         template_name: str, **kwargs) -> List[Dict[str, str]]:
        """Renders the user prompt from a template and wraps it in a standard message structure."""
        prompt = PromptManager.render(template_name, **kwargs)
        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]

    def _safe_dump(self, response: Any,
                   fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Safely dumps a Pydantic response or extracts JSON if it's GenericTextOutput."""
        try:
            if isinstance(response, GenericTextOutput):
                from ..llm.validation.json_utils import JSONExtractor
                return JSONExtractor.extract_and_repair(response.text)
            return response.model_dump()
        except Exception as e:
            logger.error(f"Failed to dump response: {e}")
            return fallback

    async def execute_with_retry(
            self, service_name: str, context: LectureContext, func, *args, **kwargs):
        """Executes a content service function with retry logic and status tracking."""
        from schemas.content import ServiceStatus
        import asyncio

        max_retries = 2
        context.status[service_name] = ServiceStatus.RUNNING

        for attempt in range(max_retries):
            try:
                result = await func(*args, **kwargs)
                context.status[service_name] = ServiceStatus.COMPLETED
                return result
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {service_name}: {e}")
                if attempt == max_retries - 1:
                    context.status[service_name] = ServiceStatus.FAILED
                    context.errors[service_name] = str(e)
                    logger.error(
                        f"Service {service_name} completely failed after {max_retries} attempts.")
                    return None
                await asyncio.sleep(2 ** attempt)

    def _chunk_segments_with_ocr(self, context: LectureContext, video_id: str, use_semantic_chunking: bool = False) -> List[Dict[str, Any]]:
        """
        Chunks transcript segments and injects relevant OCR frames into the chunks.
        Supports optional semantic boundary chunking.
        """
        segments = context.segments
        frames = context.frames
        chunks = []
        if not segments:
            return chunks

        current_text = []
        current_start = None
        current_end = 0.0
        chunk_index = 0

        for seg in segments:
            seg_start = seg.get("start", 0.0)

            if current_start is not None and current_text:
                duration = current_end - current_start
                text_len = sum(len(t) for t in current_text)

                is_boundary = False
                if use_semantic_chunking:
                    time_gap = seg_start - current_end
                    last_text = current_text[-1].strip()
                    ends_with_punctuation = last_text.endswith(('.', '?', '!', '\n'))
                    is_soft_boundary = duration >= 90.0 and (ends_with_punctuation or time_gap >= 2.0)
                    is_hard_boundary = duration >= 240.0 or text_len > 3000
                    is_boundary = is_soft_boundary or is_hard_boundary
                else:
                    is_boundary = duration >= 180.0 or text_len > 2000

                if is_boundary:
                    chunks.append({
                        "chunk_id": f"{video_id}_range_{chunk_index}",
                        "start_time": round(current_start, 2),
                        "end_time": round(current_end, 2),
                        "text": " ".join(current_text)
                    })
                    chunk_index += 1
                    current_text = []
                    current_start = None

            if current_start is None:
                current_start = seg_start

            current_text.append(seg.get("text", ""))

            if "end" in seg:
                current_end = seg["end"]
            elif "duration" in seg:
                current_end = seg_start + seg.get("duration", 0.0)
            else:
                current_end = seg_start

        if current_text:
            chunks.append({
                "chunk_id": f"{video_id}_range_{chunk_index}",
                "start_time": round(current_start, 2) if current_start is not None else 0.0,
                "end_time": round(current_end, 2),
                "text": " ".join(current_text)
            })

        # Inject OCR frames into chunks
        sorted_frames = sorted(frames or [], key=lambda f: f.get("time_sec", 0.0))
        for c in chunks:
            c_start = c["start_time"]
            c_end = c["end_time"]
            
            chunk_frames = [
                f for f in sorted_frames
                if c_start <= f.get("time_sec", 0.0) <= c_end
                and f.get("ocr", "").strip()
            ]
            
            if chunk_frames:
                ocr_text = "\n\n### Visual Content (OCR from Slides/Frames)\n\n"
                for frm in chunk_frames:
                    ts = frm.get("time_sec", 0.0)
                    scene = frm.get("scene_number", "?")
                    ocr = frm.get("ocr", "").strip()
                    ocr_text += f"**[Timestamp: {round(ts, 1)}s | Scene {scene}]**\n> {ocr}\n\n"
                
                c["text"] = c["text"] + ocr_text

        return chunks

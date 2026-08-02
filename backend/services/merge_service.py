import os
import json
import uuid
from core.utils import parse_video_id
import logging
from typing import Optional

from sqlalchemy import select

from core.config import settings
from core.database import AsyncSessionLocal
from models.transcript import Transcript
from models.vision import VideoFrame, OCRResult, FrameScore

logger = logging.getLogger(__name__)

class MergeServiceError(Exception):
    pass

class MergeService:
    async def generate_merged_markdown(self, video_id: str) -> Optional[str]:
        """
        Reads the transcript JSON and selected OCR frames from the DB,
        and generates a single markdown file containing the full transcript
        with images and OCR text injected at the appropriate timestamps.
        
        Returns the absolute path to the generated markdown file, or None if failed.
        """
        logger.info("Starting merge pipeline for video %s", video_id)
        
        async with AsyncSessionLocal() as db:
            # 1. Fetch transcript record
            t_result = await db.execute(select(Transcript).where(Transcript.video_id == parse_video_id(video_id)))
            transcript = t_result.scalar_one_or_none()
            
            if not transcript or not transcript.transcript_path or not os.path.exists(transcript.transcript_path):
                logger.warning("No transcript found for video %s, aborting merge.", video_id)
                return None
                
            # 2. Fetch selected frames with OCR results
            # Join VideoFrame -> FrameScore (is_selected=True) -> OCRResult
            f_result = await db.execute(
                select(VideoFrame, OCRResult)
                .join(FrameScore, FrameScore.frame_id == VideoFrame.id)
                .join(OCRResult, OCRResult.frame_id == VideoFrame.id, isouter=True)
                .where(VideoFrame.video_id == parse_video_id(video_id), FrameScore.is_selected == True)
                .order_by(VideoFrame.timestamp_ms.asc())
            )
            rows = f_result.all()
            
            # 3. Read Transcript JSON
            try:
                with open(transcript.transcript_path, 'r', encoding='utf-8') as f:
                    segments = json.load(f)
            except Exception as e:
                logger.error("Failed to read transcript JSON for video %s: %s", video_id, e)
                return None
                
            # 4. Align frames to segments
            # For each frame, find the segment it falls into or the nearest segment
            # We'll just attach the frame to the segment whose start/end encompasses it,
            # or the closest one if it falls outside.
            frame_attachments = {i: [] for i in range(len(segments))}
            
            for frame, ocr in rows:
                time_sec = frame.timestamp_ms / 1000.0
                
                # Find best segment
                best_idx = -1
                for i, seg in enumerate(segments):
                    start = seg.get("start", 0)
                    end = seg.get("end", 0)
                    if start <= time_sec <= end:
                        best_idx = i
                        break
                        
                if best_idx == -1 and segments:
                    # If no exact match (e.g. silence), find nearest segment by start time
                    best_idx = min(range(len(segments)), key=lambda i: abs(segments[i].get("start", 0) - time_sec))
                    
                if best_idx != -1:
                    frame_attachments[best_idx].append({
                        "path": frame.frame_path,
                        "time_sec": time_sec,
                        "ocr": ocr.clean_text if ocr and ocr.clean_text else None
                    })
                    
            # 5. Generate Markdown
            output_dir = os.path.join(settings.OUTPUT_DIR, video_id)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "merged_transcript.md")
            
            md_lines = [
                "# Complete Transcript & Notes\n",
                "> *This document contains the full transcription. Visual frames and OCR text are injected where they appear in the video.*\n",
                "---\n"
            ]
            
            for i, seg in enumerate(segments):
                # Add transcript text
                start_fmt = self._format_time(seg.get("start", 0))
                text = seg.get("text", "").strip()
                if text:
                    md_lines.append(f"**[{start_fmt}]** {text}\n")
                
                # Inject frames if any belong to this segment
                frames_here = frame_attachments.get(i, [])
                for f_data in frames_here:
                    time_fmt = self._format_time(f_data["time_sec"])
                    # Use absolute or relative path? We'll use relative to storage if served via API,
                    # but for raw markdown, we can write an absolute path or relative web path.
                    # Assuming FastAPI mounts /storage at the root, we can write a relative URL.
                    # frame_path is usually absolute or relative to project root. We need web relative.
                    # Usually frame_path is something like "../storage/frames/..."
                    # We can convert it to "/storage/frames/..."
                    web_path = f_data["path"].replace("../storage", "/storage")
                    
                    md_lines.append(f"\n### 📸 Visual Reference at {time_fmt}")
                    md_lines.append(f"![Frame at {time_fmt}]({web_path})\n")
                    
                    if f_data["ocr"]:
                        md_lines.append("> **Extracted Text:**")
                        md_lines.append(f"> {f_data['ocr']}\n")
                        
                    md_lines.append("---\n")
                    
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(md_lines))
                logger.info("Merged markdown generated successfully at %s", output_path)
                return output_path
            except Exception as e:
                logger.error("Failed to write markdown for video %s: %s", video_id, e)
                return None

    def _format_time(self, seconds: float) -> str:
        """Format seconds into HH:MM:SS or MM:SS."""
        if seconds is None:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

merge_service = MergeService()

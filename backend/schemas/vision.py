"""
Schemas for the Vision / Frame Extraction API.
"""
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class FrameMetadataSchema(BaseModel):
    blur_score: Optional[float] = None
    phash: Optional[str] = None
    duration_ms: Optional[int] = None


class OCRResultSchema(BaseModel):
    raw_text: Optional[str] = None
    clean_text: Optional[str] = None
    average_confidence: Optional[float] = None


class FrameScoreSchema(BaseModel):
    transcript_similarity: Optional[float] = None
    visual_importance_score: Optional[float] = None
    is_selected: bool = False


class VideoFrameResponse(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    timestamp_ms: int
    frame_path: str
    scene_number: int
    created_at: datetime
    metadata: Optional[FrameMetadataSchema] = None
    ocr: Optional[OCRResultSchema] = None
    score: Optional[FrameScoreSchema] = None

    class Config:
        from_attributes = True


class FrameExtractionStatus(BaseModel):
    video_id: str
    scenes: int
    frames_extracted: int
    frames_after_blur_filter: int
    frames_after_dedup: int
    frames_selected: int
    message: str = "Frame extraction complete."


class FrameDeleteResponse(BaseModel):
    video_id: str
    frames_deleted: int
    message: str

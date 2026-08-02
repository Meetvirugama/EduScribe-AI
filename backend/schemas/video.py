from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from models.video import VideoStatus, SourceType

class VideoBase(BaseModel):
    title: str
    source_type: SourceType
    youtube_url: Optional[str] = None
    thumbnail: Optional[str] = None
    channel_name: Optional[str] = None
    retention_days: int = 7

class VideoResponse(VideoBase):
    id: uuid.UUID
    status: VideoStatus
    progress_percent: Optional[int] = 0
    current_step: Optional[str] = "Initializing"
    processing_time_seconds: Optional[int] = None
    estimated_time_remaining_seconds: Optional[int] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None
    video_path: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class YoutubeRequest(BaseModel):
    url: str
    retention_days: int = 7

class VideoUpdateRetention(BaseModel):
    retention_days: int

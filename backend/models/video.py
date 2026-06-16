import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum
from core.database import Base

class VideoStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    TRANSCRIBING = "TRANSCRIBING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SourceType(str, enum.Enum):
    UPLOAD = "UPLOAD"
    YOUTUBE = "YOUTUBE"

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Using String for user_id for simplicity unless we have a users table locally
    user_id = Column(String, nullable=True) 
    title = Column(String(500), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    youtube_url = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    video_path = Column(String, nullable=True)
    thumbnail = Column(String, nullable=True)
    channel_name = Column(String, nullable=True)
    status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADING)
    progress_percent = Column(Integer, default=0)
    current_step = Column(String(100), default="Initializing")
    processing_time_seconds = Column(Integer, nullable=True)
    estimated_time_remaining_seconds = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    retention_days = Column(Integer, default=7)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

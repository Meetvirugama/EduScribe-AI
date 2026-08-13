import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from core.database import Base


class VideoStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    EXTRACTING_AUDIO = "EXTRACTING_AUDIO"
    TRANSCRIBING = "TRANSCRIBING"
    EXTRACTING_FRAMES = "EXTRACTING_FRAMES"
    RUNNING_OCR = "RUNNING_OCR"
    CHUNKING = "CHUNKING"
    MERGING_ALIGNMENT = "MERGING_ALIGNMENT"
    DETECTING_TOPICS = "DETECTING_TOPICS"
    UNDERSTANDING_CONTENT = "UNDERSTANDING_CONTENT"
    READY_FOR_SELECTION = "READY_FOR_SELECTION"
    GENERATING_ARTIFACT = "GENERATING_ARTIFACT"
    GENERATING_NOTES = "GENERATING_NOTES"
    EXPORTING = "EXPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SourceType(str, enum.Enum):
    UPLOAD = "UPLOAD"
    YOUTUBE = "YOUTUBE"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ISSUE-006: user_id must always have an owner — nullable=False enforced at DB level
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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
    # ISSUE-004: all DateTime columns are timezone-aware
    expires_at = Column(DateTime(timezone=True), nullable=True)
    # ISSUE-001: processing_started_at was missing — caused AttributeError in orchestrator.py line 95
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    # Populated at upload time; used for O(1) SQL SUM in /videos/storage
    file_size_bytes = Column(BigInteger, nullable=True)
    # ISSUE-004: timezone-aware lambda replaces deprecated datetime.utcnow
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))

    # Relationships
    user = relationship("User", backref="videos")
    transcripts = relationship("Transcript", backref="video", cascade="all, delete-orphan")
    frames = relationship("VideoFrame", backref="video", cascade="all, delete-orphan")

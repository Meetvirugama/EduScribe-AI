import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class VideoFrame(Base):
    __tablename__ = "video_frames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    timestamp_ms = Column(Integer, nullable=False)
    frame_path = Column(String, nullable=False)
    scene_number = Column(Integer, nullable=False)
    # timezone-aware datetime
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))


class FrameMetadata(Base):
    __tablename__ = "frame_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frame_id = Column(UUID(as_uuid=True), ForeignKey("video_frames.id", ondelete="CASCADE"), nullable=False)
    blur_score = Column(Float, nullable=True)
    phash = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frame_id = Column(UUID(as_uuid=True), ForeignKey("video_frames.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(String, nullable=True)
    clean_text = Column(String, nullable=True)
    average_confidence = Column(Float, nullable=True)


class FrameScore(Base):
    __tablename__ = "frame_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frame_id = Column(UUID(as_uuid=True), ForeignKey("video_frames.id", ondelete="CASCADE"), nullable=False)
    transcript_similarity = Column(Float, nullable=True)
    visual_importance_score = Column(Float, nullable=True)
    is_selected = Column(Boolean, default=False)

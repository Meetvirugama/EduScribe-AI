import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base

import enum

class TranscriptSource(str, enum.Enum):
    YOUTUBE_CAPTIONS = "youtube_captions"
    WHISPER_AUDIO = "whisper_audio"
    MANUAL_UPLOAD = "manual_upload"

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    transcript_path = Column(String, nullable=False)
    language = Column(String(20), nullable=True)
    word_count = Column(Integer, nullable=True)
    source = Column(String(50), default=TranscriptSource.WHISPER_AUDIO)
    created_at = Column(DateTime, default=datetime.utcnow)

import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from core.database import Base


class ArtifactStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    artifact_type = Column(String(100), nullable=False)  # e.g., 'quiz', 'flashcards', 'detailed_notes'
    status = Column(Enum(ArtifactStatus), default=ArtifactStatus.PENDING, nullable=False)
    
    # Store the generated content. Using JSONB since most artifacts are JSON objects.
    content = Column(JSONB, nullable=True)
    
    # Quality metrics stored as JSON
    quality = Column(JSONB, nullable=True)
    
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), onupdate=lambda: datetime.now(tz=timezone.utc))

    # Relationships
    video = relationship("Video", backref="artifacts")

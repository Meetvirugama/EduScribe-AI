"""
schemas/video.py — Pydantic request/response schemas for the Video resource.

S-13:  YoutubeRequest validates the URL at the Pydantic layer before it
       reaches the router, so invalid URLs are rejected with a 422 before any
       DB record is created (ISSUE-07 fix).

ISSUE-08: retention_days is bounded by MAX_RETENTION_DAYS at the schema level.

CS-06:  video_path (server filesystem path) is excluded from VideoResponse
        so it is never returned to the client.
"""
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse
import uuid

from models.video import VideoStatus, SourceType


# Allowed YouTube hostnames for URL validation (S-13 / ISSUE-07)
_YOUTUBE_HOSTNAMES = {
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
}

# We lazily import settings.MAX_RETENTION_DAYS in validators


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
    # CS-06: video_path intentionally excluded — server filesystem paths
    # must never be returned to clients (information disclosure).
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class YoutubeRequest(BaseModel):
    url: str
    retention_days: int = 7

    @field_validator("url")
    @classmethod
    def must_be_youtube(cls, v: str) -> str:
        """
        Reject non-YouTube URLs at the Pydantic validation layer so that
        invalid requests are rejected with a 422 before any DB record is
        created. (S-13 / ISSUE-07)
        """
        parsed = urlparse(v.strip())
        if parsed.netloc not in _YOUTUBE_HOSTNAMES:
            raise ValueError(
                "Must be a valid YouTube URL "
                "(e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)"
            )
        return v.strip()

    @field_validator("retention_days")
    @classmethod
    def clamp_retention(cls, v: int) -> int:
        """
        Enforce the maximum retention limit at the schema level (ISSUE-08).
        Clients cannot request a retention period longer than MAX_RETENTION_DAYS.
        """
        from core.config import settings
        max_days = settings.MAX_RETENTION_DAYS
        if v < 1:
            raise ValueError("retention_days must be at least 1")
        if v > max_days:
            raise ValueError(
                f"retention_days cannot exceed {max_days} days"
            )
        return v


class VideoUpdateRetention(BaseModel):
    retention_days: int

    @field_validator("retention_days")
    @classmethod
    def clamp_retention(cls, v: int) -> int:
        """Enforce max retention on updates too (ISSUE-08)."""
        from core.config import settings
        max_days = settings.MAX_RETENTION_DAYS
        if v < 1:
            raise ValueError("retention_days must be at least 1")
        if v > max_days:
            raise ValueError(
                f"retention_days cannot exceed {max_days} days"
            )
        return v

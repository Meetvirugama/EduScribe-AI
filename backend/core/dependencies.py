"""
core/dependencies.py — Shared FastAPI Dependencies

Provides reusable `Depends()` callables that are used across multiple routers.
Centralising these eliminates the repeated ownership-check pattern that
previously existed separately in video.py, notes.py, and frames.py.

Usage:
    from core.dependencies import get_owned_video

    @router.get("/{video_id}")
    async def my_endpoint(video: Video = Depends(get_owned_video)):
        ...

REF-02: Extracted from repeated ownership queries across all routers.
"""
import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from core.utils import parse_video_id
from models.user import User
from models.video import Video

logger = logging.getLogger(__name__)


async def get_owned_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Video:
    """
    FastAPI dependency that fetches a video by ID and verifies the requesting
    user owns it. Raises 404 if not found or not owned (to avoid leaking
    existence of videos belonging to other users).

    Usage:
        @router.get("/{video_id}")
        async def endpoint(video: Video = Depends(get_owned_video)):
            return video
    """
    try:
        vid_uuid = parse_video_id(video_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid video ID format.",
        )

    result = await db.execute(
        select(Video).where(
            Video.id == vid_uuid,
            Video.user_id == str(current_user.id),
        )
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found.",
        )
    return video

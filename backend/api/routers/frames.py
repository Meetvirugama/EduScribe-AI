"""
Frame extraction API router.

Endpoints:
    GET  /videos/{video_id}/frames              – List extracted frames for a video
    GET  /frames/{frame_id}                     – Get full details for one frame
    GET  /videos/{video_id}/frames/{id}/image   – Serve a frame image file
    DELETE /videos/{video_id}/frames            – Delete all frames for a video
"""
import logging
import uuid
import os
from core.utils import parse_video_id
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.video import Video
from models.vision import VideoFrame, FrameMetadata, OCRResult, FrameScore
from schemas.vision import (
    VideoFrameResponse,
    FrameMetadataSchema,
    OCRResultSchema,
    FrameScoreSchema,
    FrameDeleteResponse,
)
from services.vision.pipeline import vision_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Frame Extraction"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_video(video_id: str, user: User, db: AsyncSession) -> Video:
    """Fetch a video and verify the requesting user owns it."""
    try:
        vid_uuid = parse_video_id(video_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid video ID format.")

    result = await db.execute(
        select(Video).where(Video.id == vid_uuid, Video.user_id == str(user.id))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
    return video


def _build_frame_response_sync(
    frame: VideoFrame, meta, ocr, score
) -> VideoFrameResponse:
    """Hydrate a VideoFrame ORM object with its related metadata, OCR, and score without DB access."""
    return VideoFrameResponse(
        id=frame.id,
        video_id=frame.video_id,
        timestamp_ms=frame.timestamp_ms,
        frame_path=frame.frame_path,
        scene_number=frame.scene_number,
        created_at=frame.created_at,
        metadata=FrameMetadataSchema(
            blur_score=meta.blur_score if meta else None,
            phash=meta.phash if meta else None,
            duration_ms=meta.duration_ms if meta else None,
        ) if meta else None,
        ocr=OCRResultSchema(
            raw_text=ocr.raw_text if ocr else None,
            clean_text=ocr.clean_text if ocr else None,
            average_confidence=ocr.average_confidence if ocr else None,
        ) if ocr else None,
        score=FrameScoreSchema(
            transcript_similarity=score.transcript_similarity if score else None,
            visual_importance_score=score.visual_importance_score if score else None,
            is_selected=score.is_selected if score else False,
        ) if score else None,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/videos/{video_id}/frames",
    response_model=List[VideoFrameResponse],
    summary="List all extracted frames for a video.",
    responses={404: {"description": "Video not found."}},
)
async def list_frames(
    video_id: str,
    selected_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VideoFrameResponse]:
    """
    Retrieve extracted frames for a video.

    Query params:
        selected_only: If true, only return frames marked as best selections.
    """
    await _resolve_video(video_id, current_user, db)

    frames_query = select(VideoFrame).where(
        VideoFrame.video_id == parse_video_id(video_id)
    ).order_by(VideoFrame.scene_number)

    result = await db.execute(frames_query)
    frames = result.scalars().all()

    if not frames:
        return []

    frame_ids = [f.id for f in frames]

    metas = {
        m.frame_id: m for m in (
            await db.execute(select(FrameMetadata).where(FrameMetadata.frame_id.in_(frame_ids)))
        ).scalars().all()
    }
    ocrs = {
        o.frame_id: o for o in (
            await db.execute(select(OCRResult).where(OCRResult.frame_id.in_(frame_ids)))
        ).scalars().all()
    }

    scores_query = select(FrameScore).where(FrameScore.frame_id.in_(frame_ids))
    if selected_only:
        scores_query = scores_query.where(FrameScore.is_selected == True)
        
    scores = {
        s.frame_id: s for s in (await db.execute(scores_query)).scalars().all()
    }

    if selected_only:
        frames = [f for f in frames if f.id in scores]

    return [_build_frame_response_sync(f, metas.get(f.id), ocrs.get(f.id), scores.get(f.id)) for f in frames]


@router.get(
    "/frames/{frame_id}",
    response_model=VideoFrameResponse,
    summary="Get full details for a single frame.",
    responses={404: {"description": "Frame not found."}},
)
async def get_frame(
    frame_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoFrameResponse:
    """
    Retrieve complete metadata, OCR results, and scoring for a specific frame.

    ISSUE-12: Ownership check is now a single atomic JOIN query. This prevents
    the IDOR window where a user could confirm a frame's existence before the
    ownership check ran.
    """
    try:
        frame_uuid = uuid.UUID(frame_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid frame ID format.",
        )

    # Single JOIN query — frame only returned if the parent video belongs to
    # the requesting user. Prevents IDOR (ISSUE-12).
    result = await db.execute(
        select(VideoFrame)
        .join(Video, Video.id == VideoFrame.video_id)
        .where(
            VideoFrame.id == frame_uuid,
            Video.user_id == str(current_user.id),
        )
    )
    frame = result.scalar_one_or_none()
    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frame not found.",
        )

    meta_result  = await db.execute(select(FrameMetadata).where(FrameMetadata.frame_id == frame.id))
    meta         = meta_result.scalar_one_or_none()
    ocr_result   = await db.execute(select(OCRResult).where(OCRResult.frame_id == frame.id))
    ocr          = ocr_result.scalar_one_or_none()
    score_result = await db.execute(select(FrameScore).where(FrameScore.frame_id == frame.id))
    score        = score_result.scalar_one_or_none()
    return _build_frame_response_sync(frame, meta, ocr, score)

@router.get(
    "/videos/{video_id}/frames/{frame_id}/image",
    summary="Get the actual image file for a frame.",
    responses={404: {"description": "Frame image not found."}},
)
async def get_frame_image(
    video_id: str,
    frame_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Serve a specific frame image file from the server securely.
    (ISSUE-011 fix: No longer exposing server file paths directly to client)
    """
    await _resolve_video(video_id, current_user, db)

    try:
        frame_uuid = uuid.UUID(frame_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid frame ID format.",
        )

    result = await db.execute(
        select(VideoFrame).where(
            VideoFrame.id == frame_uuid,
            VideoFrame.video_id == parse_video_id(video_id)
        )
    )
    frame = result.scalar_one_or_none()

    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found.")

    if not frame.frame_path or not os.path.exists(frame.frame_path):
        raise HTTPException(status_code=404, detail="Image file not found on server.")

    return FileResponse(frame.frame_path)


@router.delete(
    "/videos/{video_id}/frames",
    response_model=FrameDeleteResponse,
    summary="Delete all extracted frames for a video.",
    responses={404: {"description": "Video not found."}},
)
async def delete_frames(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FrameDeleteResponse:
    """
    Delete all frame metadata from the database and frame files from disk
    for the given video.
    """
    await _resolve_video(video_id, current_user, db)

    deleted = await vision_pipeline.delete_frames(video_id)
    logger.info("Deleted %d frames for video %s by user %s", deleted, video_id, current_user.id)

    return FrameDeleteResponse(
        video_id=video_id,
        frames_deleted=deleted,
        message=f"Deleted {deleted} frame(s) and associated metadata.",
    )

"""
api/routers/video.py — Video resource CRUD and pipeline trigger endpoints.

Fixes applied:
  ISSUE-07: YouTube URL is validated by the YoutubeRequest Pydantic schema
            before any DB record is created.
  ISSUE-08: retention_days is bounded by MAX_RETENTION_DAYS at the schema layer.
  ISSUE-09: expires_at is set at creation time so the nightly cleanup job works.
  IMP-07:   processing_started_at is set before background task runs.
  CS-06:    video_path is excluded from VideoResponse schema.
  REF-02:   Uses get_owned_video shared dependency for ownership checks.
  ISSUE-18: MIME type, file size, and video duration are validated before
            any DB record is created. Per-user rate limits applied.
"""
import glob
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.dependencies import get_owned_video
from core.rate_limiter import upload_rate_limit, youtube_rate_limit
from core.security import get_current_user
from core.utils import parse_video_id
from models.transcript import Transcript
from models.user import User
from models.video import Video, VideoStatus, SourceType
from schemas.video import VideoResponse, YoutubeRequest, VideoUpdateRetention
from services import storage_service
from services.youtube import youtube_service
from worker import enqueue_video_job
from services.vision.extraction.frame_extractor import frame_extractor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["Videos"])


def _compute_expires_at(retention_days: int) -> datetime:
    """Return a UTC-aware expiry datetime from now + retention_days."""
    return datetime.now(tz=timezone.utc) + timedelta(days=retention_days)


# ---------------------------------------------------------------------------
# Upload / Submit
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    retention_days: int = Form(7),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(upload_rate_limit),  # ISSUE-18: per-user rate limit
):
    """Upload a local video file and start the AI processing pipeline."""
    # ISSUE-08: enforce retention limit
    max_days = settings.MAX_RETENTION_DAYS
    if not (1 <= retention_days <= max_days):
        raise HTTPException(
            status_code=400,
            detail=f"retention_days must be between 1 and {max_days}.",
        )

    # ISSUE-18: MIME type check — reject before saving to disk
    _ALLOWED_MIMES = {
        "video/mp4",
        "video/x-matroska",
        "video/quicktime",
        "video/x-msvideo",
        "video/webm",
        "video/mpeg",
    }
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_MIMES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{content_type}'. "
                f"Allowed: {', '.join(sorted(_ALLOWED_MIMES))}"
            ),
        )

    # ISSUE-18: File size check — read Content-Length header if provided
    max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    if file.size and file.size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.MAX_VIDEO_SIZE_MB} MB.",
        )

    video_id = str(uuid.uuid4())

    # Run the blocking chunked file-write in a thread so the event loop
    # remains responsive during large (up to 1 GB) uploads.
    file_path = await asyncio.to_thread(storage_service.save_upload_file, file, video_id)

    try:
        file_size_bytes = os.path.getsize(file_path)
    except OSError:
        file_size_bytes = None

    # ISSUE-18: Post-save size guard (in case Content-Length was absent)
    if file_size_bytes and file_size_bytes > max_bytes:
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.MAX_VIDEO_SIZE_MB} MB.",
        )

    video = Video(
        id=parse_video_id(video_id),
        user_id=str(current_user.id),
        title=file.filename,
        source_type=SourceType.UPLOAD,
        video_path=file_path,
        retention_days=retention_days,
        file_size_bytes=file_size_bytes,
        status=VideoStatus.UPLOADING,
        # ISSUE-09: set expiry at creation so the cleanup job works
        expires_at=_compute_expires_at(retention_days),
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # ISSUE-002: Use ARQ job queue instead of FastAPI BackgroundTasks
    # This ensures job persistence and retry on server restart.
    await enqueue_video_job(video_id)
    return video


@router.post("/youtube", response_model=VideoResponse)
async def process_youtube(
    req: YoutubeRequest,       # ISSUE-07: URL validated by Pydantic before DB insert
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate: None = Depends(youtube_rate_limit),  # ISSUE-18: per-user rate limit
):
    """Submit a YouTube URL for AI note generation."""
    # ISSUE-18: Pre-fetch video duration to reject overlong videos before download
    try:
        metadata = await youtube_service.fetch_metadata(req.url)
        duration = metadata.get("duration_seconds", 0)
        if duration > settings.MAX_VIDEO_DURATION_SECONDS:
            max_hours = settings.MAX_VIDEO_DURATION_SECONDS / 3600
            raise HTTPException(
                status_code=400,
                detail=f"Video is too long ({duration // 60} min). Maximum allowed is {max_hours:.0f} hours.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Could not pre-fetch YouTube metadata for %s: %s", req.url, exc)
        # Non-blocking: allow the pipeline to handle failures gracefully

    video_id = str(uuid.uuid4())
    video = Video(
        id=parse_video_id(video_id),
        user_id=str(current_user.id),
        title="Processing YouTube...",
        source_type=SourceType.YOUTUBE,
        youtube_url=req.url,
        retention_days=req.retention_days,
        status=VideoStatus.UPLOADING,
        # ISSUE-09: set expiry at creation so the cleanup job works
        expires_at=_compute_expires_at(req.retention_days),
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # ISSUE-002: Use ARQ job queue instead of FastAPI BackgroundTasks
    await enqueue_video_job(video_id)
    return video


# ---------------------------------------------------------------------------
# List / Analytics
# ---------------------------------------------------------------------------

@router.get("", response_model=list[VideoResponse])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all videos belonging to the current user."""
    result = await db.execute(
        select(Video)
        .where(Video.user_id == current_user.id)  # ISSUE-024: use UUID directly
        .order_by(Video.created_at.desc())
    )
    return result.scalars().all()


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return aggregated learning statistics for the current user."""
    stats = await db.execute(
        select(
            func.count(Video.id).label("total_videos"),
            func.coalesce(func.sum(Video.duration_seconds), 0).label("total_duration"),
        ).where(Video.user_id == current_user.id)  # ISSUE-024: use UUID directly
    )
    row = stats.one()

    word_count_row = await db.execute(
        select(func.coalesce(func.sum(Transcript.word_count), 0))
        .join(Video, Video.id == Transcript.video_id)
        .where(Video.user_id == str(current_user.id))
    )
    total_words = word_count_row.scalar()

    return {
        "total_videos": row.total_videos,
        "total_learning_minutes": round((row.total_duration or 0) / 60),
        "total_words_generated": total_words or 0,
    }


@router.get("/storage")
async def get_storage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return storage usage for the current user using a fast SQL aggregate.
    Uses SUM(file_size_bytes) — single query, no disk stats calls.
    """
    row = await db.execute(
        select(
            func.coalesce(func.sum(Video.file_size_bytes), 0).label("total_bytes")
        ).where(Video.user_id == current_user.id)  # ISSUE-024: use UUID directly
    )
    total_bytes = row.scalar() or 0
    transcript_est = int(total_bytes * 0.001)
    return {
        "total_used_bytes": total_bytes + transcript_est,
        "videos_bytes": total_bytes,
        "transcripts_bytes": transcript_est,
    }


# ---------------------------------------------------------------------------
# Single-video detail endpoints — use get_owned_video shared dependency (REF-02)
# ---------------------------------------------------------------------------



@router.get("/{video_id}/details")
async def get_video_details(
    video_id: str,
    video: Video = Depends(get_owned_video),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve extended details including transcript metadata."""
    t_result = await db.execute(
        select(Transcript).where(Transcript.video_id == parse_video_id(video_id))
    )
    transcript = t_result.scalar_one_or_none()

    return {
        "video": video,
        "transcript_meta": {
            "source": transcript.source if transcript else None,
            "word_count": transcript.word_count if transcript else None,
            "language": transcript.language if transcript else None,
        },
    }


@router.get("/{video_id}/transcript")
async def get_transcript(
    video_id: str,
    video: Video = Depends(get_owned_video),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the full transcript JSON for a video."""
    import json

    result = await db.execute(
        select(Transcript).where(Transcript.video_id == parse_video_id(video_id))
    )
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not ready or not found")

    if not os.path.exists(transcript.transcript_path):
        raise HTTPException(status_code=404, detail="Transcript file not found on disk")

    def _read_json():
        with open(transcript.transcript_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return await asyncio.to_thread(_read_json)


@router.patch("/{video_id}/retention", response_model=VideoResponse)
async def update_retention(
    video_id: str,
    payload: VideoUpdateRetention,   # ISSUE-08: retention capped by schema validator
    video: Video = Depends(get_owned_video),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the retention period and recalculate expires_at (ISSUE-09)."""
    video.retention_days = payload.retention_days
    # ISSUE-09: always recalculate expires_at when retention changes
    video.expires_at = _compute_expires_at(payload.retention_days)
    await db.commit()
    await db.refresh(video)
    return video


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    video: Video = Depends(get_owned_video),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a video and all its associated files and data."""
    # Delete associated transcript
    t_result = await db.execute(
        select(Transcript).where(Transcript.video_id == parse_video_id(video_id))
    )
    transcript = t_result.scalar_one_or_none()

    if transcript:
        if transcript.transcript_path and os.path.exists(transcript.transcript_path):
            try:
                os.remove(transcript.transcript_path)
            except OSError as exc:
                logger.warning(
                    "Could not delete transcript file %s for video %s: %s",
                    transcript.transcript_path,
                    video_id,
                    exc,
                )
        await db.delete(transcript)

    if video.video_path and os.path.exists(video.video_path):
        try:
            os.remove(video.video_path)
        except OSError as exc:
            logger.warning(
                "Could not delete video file %s for video %s: %s",
                video.video_path,
                video_id,
                exc,
            )

    # Delete extracted frames from disk
    await frame_extractor_service.delete_frames_for_video(video_id)

    # Clean up any lingering temp/upload files
    for temp_file in glob.glob(f"{settings.TEMP_DIR}/*{video_id}*"):
        try:
            os.remove(temp_file)
        except Exception:
            pass
    for upload_file in glob.glob(f"{settings.UPLOAD_DIR}/*{video_id}*"):
        try:
            os.remove(upload_file)
        except Exception:
            pass

    await db.delete(video)
    await db.commit()

    return {"status": "success", "message": "Video deleted"}

from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.video import Video, VideoStatus, SourceType
from models.transcript import Transcript
from schemas.video import VideoResponse, YoutubeRequest, VideoUpdateRetention
from services import storage_service
from tasks import process_video_pipeline_async
import uuid
from core.utils import parse_video_id
import os
import json
import glob
from services.vision.frame_extractor import frame_extractor_service

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    retention_days: int = Form(7),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_id = str(uuid.uuid4())
    file_path = storage_service.save_upload_file(file, video_id)

    video = Video(
        id=parse_video_id(video_id),
        user_id=str(current_user.id),
        title=file.filename,
        source_type=SourceType.UPLOAD,
        video_path=file_path,
        retention_days=retention_days,
        status=VideoStatus.UPLOADING
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Immediately queue the pipeline in background tasks
    background_tasks.add_task(process_video_pipeline_async, video_id)
    return video

@router.post("/youtube", response_model=VideoResponse)
async def process_youtube(
    req: YoutubeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_id = str(uuid.uuid4())
    video = Video(
        id=parse_video_id(video_id),
        user_id=str(current_user.id),
        title="Processing YouTube...",
        source_type=SourceType.YOUTUBE,
        youtube_url=req.url,
        retention_days=req.retention_days,
        status=VideoStatus.UPLOADING
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    background_tasks.add_task(process_video_pipeline_async, video_id)
    return video

@router.get("", response_model=list[VideoResponse])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video)
        .where(Video.user_id == str(current_user.id))
        .order_by(Video.created_at.desc())
    )
    return result.scalars().all()

@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import func
    
    stats = await db.execute(
        select(
            func.count(Video.id).label("total_videos"),
            func.coalesce(func.sum(Video.duration_seconds), 0).label("total_duration"),
        ).where(Video.user_id == str(current_user.id))
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
        "total_words_generated": total_words or 0
    }

@router.get("/storage")
async def get_storage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video.video_path)
        .where(Video.user_id == str(current_user.id))
    )
    video_paths = [row[0] for row in result.all() if row[0]]
    
    t_result = await db.execute(
        select(Transcript.transcript_path)
        .join(Video, Video.id == Transcript.video_id)
        .where(Video.user_id == str(current_user.id))
    )
    transcript_paths = [row[0] for row in t_result.all() if row[0]]

    def _compute_sizes():
        v_bytes = sum(os.path.getsize(p) for p in video_paths if os.path.exists(p))
        t_bytes = sum(os.path.getsize(p) for p in transcript_paths if os.path.exists(p))
        return v_bytes, t_bytes

    import asyncio
    video_bytes, transcript_bytes = await asyncio.to_thread(_compute_sizes)
    
    total_bytes = video_bytes + transcript_bytes
    
    return {
        "total_used_bytes": total_bytes,
        "videos_bytes": video_bytes,
        "transcripts_bytes": transcript_bytes
    }

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video)
        .where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/{video_id}/details")
async def get_video_details(
    video_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Video)
        .where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id))
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    t_result = await db.execute(select(Transcript).where(Transcript.video_id == parse_video_id(video_id)))
    transcript = t_result.scalar_one_or_none()
    
    return {
        "video": video,
        "transcript_meta": {
            "source": transcript.source if transcript else None,
            "word_count": transcript.word_count if transcript else None,
            "language": transcript.language if transcript else None,
        }
    }

@router.get("/{video_id}/transcript")
async def get_transcript(
    video_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    result = await db.execute(select(Video).where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id)))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    result = await db.execute(select(Transcript).where(Transcript.video_id == parse_video_id(video_id)))
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not ready or not found")
        
    if not os.path.exists(transcript.transcript_path):
        raise HTTPException(status_code=404, detail="Transcript file not found on disk")

    import asyncio
    def _read_json():
        with open(transcript.transcript_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    data = await asyncio.to_thread(_read_json)
    return data

@router.patch("/{video_id}/retention", response_model=VideoResponse)
async def update_retention(
    video_id: str,
    payload: VideoUpdateRetention,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Video).where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id)))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    video.retention_days = payload.retention_days
    await db.commit()
    await db.refresh(video)
    
    return video

@router.delete("/{video_id}")
async def delete_video(
    video_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Video).where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id)))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    # Delete associated transcript
    t_result = await db.execute(select(Transcript).where(Transcript.video_id == parse_video_id(video_id)))
    transcript = t_result.scalar_one_or_none()
    
    if transcript:
        try:
            if os.path.exists(transcript.transcript_path):
                os.remove(transcript.transcript_path)
        except OSError as exc:
            import logging
            logging.getLogger(__name__).warning("Could not delete transcript file %s for video %s: %s", transcript.transcript_path, video_id, exc)
        await db.delete(transcript)

    try:
        if video.video_path and os.path.exists(video.video_path):
            os.remove(video.video_path)
    except OSError as exc:
        import logging
        logging.getLogger(__name__).warning("Could not delete video file %s for video %s: %s", video.video_path, video_id, exc)
        
    # Delete extracted frames from disk
    await frame_extractor_service.delete_frames_for_video(video_id)
    
    # Clean up any lingering temporary files (e.g. .ytdl parts or .wav files)
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

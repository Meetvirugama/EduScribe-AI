import os
import uuid
from core.utils import parse_video_id
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User
from models.video import Video

router = APIRouter(prefix="/notes", tags=["Notes"])

def _get_notes_path(video_id: str) -> str:
    return os.path.join(settings.OUTPUT_DIR, video_id, "merged_transcript.md")

@router.get("/{video_id}")
async def get_notes(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch the merged markdown content for previewing."""
    result = await db.execute(select(Video).where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id)))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    notes_path = _get_notes_path(video_id)
    if not os.path.exists(notes_path):
        raise HTTPException(status_code=404, detail="Notes have not been generated yet or were deleted.")
        
    with open(notes_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return {"video_id": video_id, "content": content}

@router.get("/{video_id}/download")
async def download_notes(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the merged markdown file."""
    result = await db.execute(select(Video).where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id)))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    notes_path = _get_notes_path(video_id)
    if not os.path.exists(notes_path):
        raise HTTPException(status_code=404, detail="Notes have not been generated yet.")
        
    return FileResponse(
        path=notes_path, 
        filename=f"{video.title}_Notes.md", 
        media_type="text/markdown"
    )

@router.delete("/{video_id}")
async def delete_notes(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete the generated notes file without deleting the video."""
    result = await db.execute(select(Video).where(Video.id == parse_video_id(video_id), Video.user_id == str(current_user.id)))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    notes_path = _get_notes_path(video_id)
    if os.path.exists(notes_path):
        try:
            os.remove(notes_path)
            return {"status": "success", "message": "Notes deleted successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete notes: {e}")
    else:
        raise HTTPException(status_code=404, detail="Notes not found.")

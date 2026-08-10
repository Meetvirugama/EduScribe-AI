"""
api/routers/notes.py — Notes retrieval, search, download, and deletion endpoints.

Fixes applied:
  MEDIUM-005 / REF-02: Use get_owned_video shared dependency instead of
                        repeating the ownership-check query in each endpoint.
  HIGH-006  / SEC-003: Don't leak raw exception text to the client; log
                        server-side and return a generic message.
  MEDIUM-006 / SEC-004: Sanitize video.title before using it in the
                        Content-Disposition filename to avoid header issues
                        with untrusted titles from YouTube or user uploads.
"""
import os
import re
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, AsyncSessionLocal
from core.dependencies import get_owned_video
from core.config import settings
from models.video import Video
from services.rag.pipeline import vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notes", tags=["Notes"])

_UNSAFE_FILENAME_CHARS = re.compile(r'[^\w\s\-.]')


def _get_notes_path(video_id: str) -> str:
    return os.path.join(settings.OUTPUT_DIR, video_id, "merged_transcript.md")


def _safe_filename(title: str) -> str:
    """Strip characters that are unsafe in Content-Disposition filenames."""
    sanitized = _UNSAFE_FILENAME_CHARS.sub('', title).strip()
    return sanitized or "Notes"


@router.get("/{video_id}")
async def get_notes(
    video: Video = Depends(get_owned_video),
):
    """Fetch the merged markdown content for previewing."""
    notes_path = _get_notes_path(str(video.id))
    if not os.path.exists(notes_path):
        raise HTTPException(status_code=404, detail="Notes have not been generated yet or were deleted.")

    def _read_file():
        with open(notes_path, "r", encoding="utf-8") as f:
            return f.read()

    content = await asyncio.to_thread(_read_file)
    return {"video_id": str(video.id), "content": content}


@router.get("/{video_id}/search")
async def search_notes(
    query: str,
    video: Video = Depends(get_owned_video),
):
    """Semantic search across the generated notes."""
    if len(query) > 500:
        raise HTTPException(status_code=400, detail="Query too long (max 500 characters)")

    try:
        results = await vector_store.search(str(video.id), query)
        return {"video_id": str(video.id), "query": query, "results": results}
    except Exception as exc:
        logger.error("search_notes: search failed for video %s: %s", video.id, exc)
        raise HTTPException(status_code=500, detail="Search failed. Please try again later.")


@router.get("/{video_id}/download")
async def download_notes(
    video: Video = Depends(get_owned_video),
):
    """Download the merged markdown file."""
    notes_path = _get_notes_path(str(video.id))
    if not os.path.exists(notes_path):
        raise HTTPException(status_code=404, detail="Notes have not been generated yet.")

    safe_title = _safe_filename(video.title or "")
    return FileResponse(
        path=notes_path,
        filename=f"{safe_title}_Notes.md",
        media_type="text/markdown",
    )


@router.delete("/{video_id}")
async def delete_notes(
    video: Video = Depends(get_owned_video),
):
    """Delete the generated notes file without deleting the video."""
    notes_path = _get_notes_path(str(video.id))
    if os.path.exists(notes_path):
        try:
            await asyncio.to_thread(os.remove, notes_path)
            return {"status": "success", "message": "Notes deleted successfully."}
        except Exception as exc:
            logger.error("delete_notes: failed to delete notes for video %s: %s", video.id, exc)
            raise HTTPException(status_code=500, detail="Failed to delete notes. Please try again later.")
    else:
        raise HTTPException(status_code=404, detail="Notes not found.")

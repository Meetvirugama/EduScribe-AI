"""
api/routers/progress.py — Real-Time Progress Streaming (SSE)

Provides a Server-Sent Events endpoint that streams video processing
progress updates to the frontend in real-time without polling.

The frontend connects once; updates are pushed as the pipeline advances
through each stage. The stream closes automatically on COMPLETED or FAILED.

Issue Resolved: #19 (missing processing progress tracking)

Requires: sse-starlette (add to requirements.txt)
    pip install sse-starlette
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, AsyncSessionLocal
from core.security import get_current_user
from core.utils import parse_video_id
from models.user import User
from models.video import Video, VideoStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["Progress"])

# Poll interval in seconds (balance between responsiveness and DB load)
_POLL_INTERVAL = 2.0

# Terminal states — stream closes when reached
_TERMINAL_STATES = {VideoStatus.COMPLETED, VideoStatus.FAILED}


@router.get("/{video_id}/progress/stream")
async def stream_progress(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stream real-time processing progress for a video via Server-Sent Events.

    The client connects with:
        const source = new EventSource('/videos/{id}/progress/stream');
        source.onmessage = (e) => console.log(JSON.parse(e.data));

    Each event payload:
        {
          "status": "GENERATING_NOTES",
          "progress": 80,
          "step": "Enriching Knowledge (Phase 3-4)",
          "video_id": "..."
        }

    The stream automatically closes when status is COMPLETED or FAILED.
    """
    # Verify ownership before opening the stream
    result = await db.execute(
        select(Video).where(
            Video.id == parse_video_id(video_id),
            Video.user_id == current_user.id,
        )
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    try:
        from sse_starlette.sse import EventSourceResponse  # type: ignore
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="SSE not available. Install sse-starlette: pip install sse-starlette",
        )

    async def _event_generator() -> AsyncGenerator[dict, None]:
        while True:
            try:
                # Open a fresh, short-lived session per poll so we never hold
                # the Depends-injected session open for the full stream duration
                # (HIGH-002 / PERF-001: avoids connection pool exhaustion).
                async with AsyncSessionLocal() as poll_db:
                    res = await poll_db.execute(
                        select(Video).where(Video.id == parse_video_id(video_id))
                    )
                    current = res.scalar_one_or_none()

                if current is None:
                    yield {
                        "data": json.dumps({
                            "error": "Video not found",
                            "video_id": video_id,
                        })
                    }
                    break

                payload = {
                    "video_id": video_id,
                    "status": current.status.value if current.status else "UNKNOWN",
                    "progress": current.progress_percent or 0,
                    "step": current.current_step or "",
                    "error": current.error_message if current.status == VideoStatus.FAILED else None,
                }

                yield {"data": json.dumps(payload)}

                if current.status in _TERMINAL_STATES:
                    logger.info(
                        "progress/stream: closing stream for video %s (status=%s)",
                        video_id, current.status,
                    )
                    break

                await asyncio.sleep(_POLL_INTERVAL)

            except asyncio.CancelledError:
                logger.info("progress/stream: client disconnected for video %s", video_id)
                break
            except Exception as exc:
                logger.error("progress/stream: error for video %s: %s", video_id, exc)
                yield {"data": json.dumps({"error": str(exc), "video_id": video_id})}
                break

    return EventSourceResponse(_event_generator())

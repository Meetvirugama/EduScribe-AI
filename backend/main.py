"""
main.py — FastAPI Application Entry Point

Security / architecture fixes applied:
  ISSUE-10:  CORS origins read from settings; methods and headers are explicit,
             not wildcard.
  ISSUE-11:  Storage directory created using settings.UPLOAD_DIR (not a
             relative ../storage string).
  ISSUE-16:  Static file mount removed. Storage files are served through
             authenticated API endpoints that verify ownership.
  S-12:      Global exception handler added to log unhandled errors and return
             structured 500 responses without leaking internals.
  S-04:      Structured logging format with level and module name.
"""
import logging
import os
import traceback
import uuid

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.routers import video, auth
from api.routers import frames as frames_router
from api.routers import admin as admin_router
from api.routers import progress as progress_router
from api.routers import generate as generate_router
from core.config import settings

# ---------------------------------------------------------------------------
# Logging configuration  (S-04)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(funcName)s: %(message)s",
)
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


# ---------------------------------------------------------------------------
# Nightly cleanup job
# ---------------------------------------------------------------------------

async def cleanup_expired_videos() -> None:
    """
    Nightly job that deletes all videos past their retention expiry.

    Runs at 02:00 every night. For each expired video it:
      1. Deletes transcript file from disk
      2. Deletes video file from disk
      3. Deletes extracted frames directory from disk
      4. Deletes all DB records (cascades to transcripts, frames, scores via FK)

    ISSUE-09: This job now works correctly because expires_at is set at
              video creation time (previously it was always NULL).
    """
    from datetime import datetime, timezone
    from sqlalchemy import select
    from core.database import AsyncSessionLocal
    from models.video import Video
    from models.transcript import Transcript
    from services.vision.pipeline import vision_pipeline
    import glob

    logger.info("Running nightly expired-video cleanup job...")
    deleted_count = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(
                Video.expires_at.is_not(None),
                Video.expires_at < datetime.now(tz=timezone.utc),
            )
        )
        expired_videos = result.scalars().all()

        for video in expired_videos:
            video_id = str(video.id)
            try:
                # 1. Delete transcript file
                t_result = await db.execute(
                    select(Transcript).where(Transcript.video_id == video.id)
                )
                transcript = t_result.scalar_one_or_none()
                if transcript and transcript.transcript_path and os.path.exists(transcript.transcript_path):
                    try:
                        os.remove(transcript.transcript_path)
                    except OSError as e:
                        logger.warning("Could not remove transcript for %s: %s", video_id, e)

                # 2. Delete video file
                if video.video_path and os.path.exists(video.video_path):
                    try:
                        os.remove(video.video_path)
                    except OSError as e:
                        logger.warning("Could not remove video file for %s: %s", video_id, e)

                # 3. Delete frames from disk
                await vision_pipeline.delete_frames(video_id)

                # 4. Clean up temp/upload leftovers
                for tmp in glob.glob(f"{settings.TEMP_DIR}/*{video_id}*"):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
                for upl in glob.glob(f"{settings.UPLOAD_DIR}/*{video_id}*"):
                    try:
                        os.remove(upl)
                    except Exception:
                        pass

                # 5. ISSUE-15: Delete AI artifacts — embeddings, RAG index, outputs
                _ai_artifact_dirs = [
                    os.path.join(settings.EMBEDDING_DIR, video_id),  # embedding vectors
                    os.path.join(settings.OUTPUT_DIR, video_id),      # merged markdown + RAG index
                ]
                for artifact_dir in _ai_artifact_dirs:
                    if os.path.isdir(artifact_dir):
                        import shutil
                        try:
                            shutil.rmtree(artifact_dir)
                            logger.info("Deleted AI artifact dir for %s: %s", video_id, artifact_dir)
                        except OSError as e:
                            logger.warning("Could not remove AI artifact dir %s: %s", artifact_dir, e)

                # 6. ISSUE-15: Delete OCR temp files (named by video_id)
                for ocr_tmp in glob.glob(f"{settings.FRAMES_DIR}/{video_id}*"):
                    try:
                        if os.path.isdir(ocr_tmp):
                            import shutil
                            shutil.rmtree(ocr_tmp)
                        else:
                            os.remove(ocr_tmp)
                    except Exception:
                        pass

                # 7. Delete DB record (cascades to transcripts, frames, scores)
                await db.delete(video)
                deleted_count += 1

            except Exception as e:
                logger.error("Failed to clean up expired video %s: %s", video_id, e)

        await db.commit()

    logger.info("Nightly cleanup complete. Deleted %d expired video(s).", deleted_count)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all storage directories exist on startup (ISSUE-11 — use settings paths)
    for storage_dir in [
        settings.UPLOAD_DIR,
        settings.OUTPUT_DIR,
        settings.TEMP_DIR,
        settings.TRANSCRIPT_DIR,
        settings.FRAMES_DIR,
    ]:
        os.makedirs(storage_dir, exist_ok=True)

    # Start nightly cleanup scheduler (runs at 02:00 every day)
    scheduler.add_job(
        cleanup_expired_videos,
        trigger=CronTrigger(hour=2, minute=0),
        id="cleanup_expired_videos",
        replace_existing=True,
        misfire_grace_time=3600,  # allow up to 1h late if server was down
    )
    scheduler.start()
    logger.info("APScheduler started — nightly cleanup scheduled at 02:00.")

    yield

    scheduler.shutdown(wait=False)
    logger.info("APScheduler shut down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="EduScribe AI API",
    description="YouTube-to-Notes AI backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ISSUE-16: Static file mount REMOVED. Frame images and generated notes must
# be accessed through authenticated endpoints in the respective routers.
# (Previously: app.mount("/storage", StaticFiles(...), name="storage"))

# ISSUE-10: CORS — origins from settings, explicit methods/headers only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(video.router)
app.include_router(auth.router)
app.include_router(frames_router.router)
app.include_router(admin_router.router)
app.include_router(progress_router.router)
app.include_router(generate_router.router)


# ---------------------------------------------------------------------------
# Global exception handler (S-12)
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.
    Logs the full traceback with a request-correlation ID and returns a
    generic 500 body — never leaking internal paths or stack traces to clients.
    """
    request_id = str(uuid.uuid4())
    logger.error(
        "Unhandled exception [request_id=%s] %s %s: %s\n%s",
        request_id,
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        },
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "EduScribe AI Backend is running"}

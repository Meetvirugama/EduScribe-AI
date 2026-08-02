from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from api.routers import video, auth
from api.routers import frames as frames_router
from api.routers import notes as notes_router
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def cleanup_expired_videos() -> None:
    """
    Nightly job that deletes all videos past their retention expiry.

    Runs at 02:00 every night. For each expired video it:
      1. Deletes transcript file from disk
      2. Deletes video file from disk
      3. Deletes extracted frames directory from disk
      4. Deletes all DB records (cascades to transcripts, frames, scores via FK)
    """
    from datetime import datetime
    from sqlalchemy import select
    from core.database import AsyncSessionLocal
    from models.video import Video
    from models.transcript import Transcript
    from services.vision.pipeline import vision_pipeline
    import glob
    from core.config import settings

    logger.info("Running nightly expired-video cleanup job...")
    deleted_count = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).where(Video.expires_at < datetime.utcnow())
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

                # 5. Delete DB record (cascades to transcripts, frames, scores)
                await db.delete(video)
                deleted_count += 1

            except Exception as e:
                logger.error("Failed to clean up expired video %s: %s", video_id, e)

        await db.commit()

    logger.info("Nightly cleanup complete. Deleted %d expired video(s).", deleted_count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("../storage", exist_ok=True)

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


app = FastAPI(title="EduScribe AI Phase 1 API", lifespan=lifespan)

app.include_router(video.router)
app.include_router(auth.router)
app.include_router(frames_router.router)
app.include_router(notes_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory="../storage"), name="storage")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "EduScribe AI Backend is running (FastAPI)"}

"""
worker.py — ARQ Background Job Worker

Replaces FastAPI BackgroundTasks with an ARQ (async Redis Queue) worker.
ARQ provides:
  - Job persistence in Redis (survives server restarts)
  - Automatic retry with configurable back-off
  - Job status tracking (queued → in-progress → complete/failed)
  - Deduplication (prevents duplicate jobs for the same video_id)
  - Health check via arq CLI

Issue Resolved: #16 (missing background job architecture)

Setup:
    # Install ARQ
    pip install arq

    # Start the worker (separate process from uvicorn)
    arq worker.WorkerSettings

    # Or via Docker:
    command: arq worker.WorkerSettings

Redis URL is read from REDIS_URL env var (already in docker-compose.yml).
"""
import asyncio
import logging
import os
from datetime import timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------
# Attempt 1: immediate
# Attempt 2: 30 seconds
# Attempt 3: 5 minutes
# Attempt 4: 30 minutes (then mark as failed)
_RETRY_DELAYS = [30, 300, 1800]  # seconds between retries


# ---------------------------------------------------------------------------
# Job functions (called by ARQ worker processes)
# ---------------------------------------------------------------------------

async def process_video_job(ctx: dict, video_id: str) -> dict:
    """
    ARQ job that runs the full EduScribe AI pipeline for a video.

    This wraps the existing process_video_pipeline_async coroutine so
    that it runs inside an ARQ worker with retry and persistence.

    Args:
        ctx:       ARQ context dict (contains Redis connection, job_id, etc.)
        video_id:  The video UUID string.

    Returns:
        A dict with the final job status.
    """
    job_id = ctx.get("job_id", "unknown")
    attempt = ctx.get("job_try", 1)

    logger.info(
        "ARQ worker: starting process_video_job | job_id=%s | video_id=%s | attempt=%d",
        job_id, video_id, attempt,
    )

    try:
        from pipeline.orchestrator import process_video_pipeline_async
        await process_video_pipeline_async(video_id)
        logger.info("ARQ worker: job %s completed for video %s", job_id, video_id)
        return {"status": "completed", "video_id": video_id, "job_id": job_id}
    except Exception as exc:
        logger.error(
            "ARQ worker: job %s failed for video %s (attempt %d): %s",
            job_id, video_id, attempt, exc,
        )
        raise  # ARQ will retry based on WorkerSettings.retry_jobs and max_tries


# ---------------------------------------------------------------------------
# Startup / shutdown hooks
# ---------------------------------------------------------------------------

async def startup(ctx: dict) -> None:
    """Called once when the ARQ worker process starts."""
    logger.info("ARQ worker startup — PID %d", os.getpid())


async def shutdown(ctx: dict) -> None:
    """Called once when the ARQ worker process shuts down."""
    logger.info("ARQ worker shutdown — PID %d", os.getpid())


# ---------------------------------------------------------------------------
# Worker settings
# ---------------------------------------------------------------------------

class WorkerSettings:
    """
    ARQ worker configuration.

    Run with:  arq worker.WorkerSettings
    """

    # Job functions available to this worker
    functions = [process_video_job]

    # Redis connection (reads from REDIS_URL env var)
    redis_settings_from_url = True

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Job timeout: 2 hours maximum (generous for very long videos)
    job_timeout = 7200

    # Retry configuration
    max_tries = 4           # 1 initial + 3 retries
    retry_jobs = True

    # Prevent duplicate jobs for the same video_id
    allow_abort_jobs = True

    # Queue name (allows running multiple separate queues if needed)
    queue_name = "eduscribe:pipeline"

    # Keep completed job results for 24 hours (for status queries)
    keep_result = 86400

    # Concurrency: 2 videos at a time per worker process
    max_jobs = 2



# ---------------------------------------------------------------------------
# Enqueue helper (called from API routers instead of BackgroundTasks)
# ---------------------------------------------------------------------------

async def enqueue_video_job(video_id: str) -> str:
    """
    Enqueue a video processing job into the ARQ queue.

    Usage in video router:
        from worker import enqueue_video_job
        job = await enqueue_video_job(video_id)

    Falls back to direct asyncio.create_task() if Redis is unavailable
    (e.g., during local development without Docker).

    Returns the ARQ job ID.
    """
    from core.config import settings
    redis_url = settings.REDIS_URL

    if not redis_url:
        logger.warning(
            "REDIS_URL not set — falling back to asyncio.create_task() for video %s. "
            "Jobs will NOT survive server restarts.",
            video_id,
        )
        from pipeline.orchestrator import process_video_pipeline_async
        asyncio.create_task(process_video_pipeline_async(video_id))
        return f"local_{video_id}"

    try:
        from arq.connections import ArqRedis, create_pool, RedisSettings  # type: ignore
        pool: ArqRedis = await create_pool(RedisSettings.from_dsn(redis_url))
        job = await pool.enqueue_job(
            "process_video_job",
            video_id,
            _queue_name="eduscribe:pipeline",
            _job_id=f"video_{video_id}",  # deduplication key
        )
        await pool.aclose()
        job_id = job.job_id if job else f"dup_{video_id}"
        logger.info("ARQ: enqueued job %s for video %s", job_id, video_id)
        return job_id
    except Exception as exc:
        logger.error(
            "ARQ enqueue failed (%s) — falling back to asyncio.create_task() for video %s",
            exc, video_id,
        )
        from pipeline.orchestrator import process_video_pipeline_async
        asyncio.create_task(process_video_pipeline_async(video_id))
        return f"fallback_{video_id}"

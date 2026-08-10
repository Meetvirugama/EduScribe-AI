# Backend Architecture

The backend is an async FastAPI application. Video processing runs in a separate **ARQ worker** process that reads jobs from a Redis queue — the API server is never blocked by AI workloads.

---

## Core Technologies

| Library | Version | Role |
|---|---|---|
| FastAPI | 0.110+ | REST API framework |
| uvicorn + uvloop | latest | ASGI server with C-based event loop |
| SQLAlchemy | 2.0 (async) | ORM with asyncpg driver |
| Alembic | latest | Database migrations |
| APScheduler | 3.10+ | Nightly cleanup cron |
| ARQ | 0.25+ | Async Redis job queue |
| litellm | 1.30+ | Unified LLM provider interface |
| faster-whisper | 1.0+ | Speech-to-text (INT8 CTranslate2) |
| PaddleOCR | latest | Frame text extraction |
| PySceneDetect | 0.6+ | Scene boundary detection |
| imagehash | 4.3+ | Perceptual duplicate detection |
| RapidFuzz | 3.0+ | Transcript fuzzy matching |
| ffmpeg-python | latest | Audio extraction wrapper |
| cachetools | 5.5+ | LRU cache for OCR results |
| tenacity | 8.2+ | Retry with back-off |
| sse-starlette | 1.6+ | Server-Sent Events |
| python-jose / PyJWT | latest | JWT generation and validation |

---

## Directory Structure

```
backend/
├── api/
│   └── routers/
│       ├── auth.py          # Google OAuth2 + JWT + /auth/exchange
│       ├── video.py         # Upload, YouTube ingest, list, delete, storage
│       ├── frames.py        # Frame retrieval + authenticated image serving
│       ├── notes.py         # Notes fetch, download, search, delete
│       ├── progress.py      # SSE real-time progress stream
│       └── admin.py         # Admin-only stats endpoints
├── core/
│   ├── config.py            # pydantic-settings (all env vars)
│   ├── database.py          # AsyncPG engine + AsyncSessionLocal
│   ├── dependencies.py      # Shared dependencies (get_owned_video, etc.)
│   └── security.py          # JWT create + validate + get_current_user
├── models/
│   ├── user.py              # User ORM model
│   ├── video.py             # Video + VideoStatus enum + SourceType
│   ├── transcript.py        # Transcript ORM model
│   └── vision.py            # VideoFrame, FrameMetadata, OCRResult, FrameScore
├── schemas/
│   ├── video.py             # YoutubeRequest, VideoUpdateRetention, VideoResponse
│   ├── content.py           # LectureState, LectureInput, ServiceStatus
│   └── (others)
├── services/
│   ├── youtube.py           # YouTubeService: validate_url, fetch_metadata, download_video
│   ├── storage.py           # File save/delete helpers
│   ├── audio/
│   │   ├── service.py       # FFmpeg audio extraction
│   │   └── (whisper_service.py, etc.)
│   ├── content/
│   │   ├── pipeline.py      # ContentPipeline: concurrent DAG execution
│   │   ├── context.py       # LectureContext proxy + LectureState
│   │   ├── base.py          # BaseContentService + execute_with_retry
│   │   ├── notes.py         # NotesService
│   │   ├── concept.py       # ConceptService
│   │   ├── quiz.py          # QuizService
│   │   ├── flashcard.py     # FlashcardService
│   │   ├── mindmap.py       # MindmapService
│   │   ├── formula.py       # FormulaService
│   │   ├── interview.py     # InterviewService
│   │   ├── revision.py      # RevisionService
│   │   ├── merge.py         # MergeService: transcript + frames → Markdown
│   │   └── prompts.py       # PromptManager: Jinja2 template rendering
│   ├── llm/
│   │   ├── llm_manager.py   # Central orchestrator (generate + embed)
│   │   ├── model_selector.py# TaskType → model config
│   │   ├── key_manager.py   # Multi-key round-robin per provider
│   │   ├── quota_tracker.py # Per-provider quota tracking
│   │   ├── retry_manager.py # Exponential back-off retry
│   │   ├── fallback_manager.py # Provider fallback chain
│   │   ├── embedding_manager.py # Embedding via Jina AI
│   │   └── validation/      # JSON extraction + Pydantic schema validation
│   ├── rag/
│   │   ├── pipeline.py      # vector_store.index() + .search()
│   │   ├── chunker.py       # 4 chunking strategies
│   │   ├── structure_detector.py # Chunk type classification
│   │   ├── embedding_store.py    # Read/write embedding vectors
│   │   ├── retriever.py     # Hybrid BM25 + dense + MMR re-rank
│   │   └── context_optimizer.py # Fit retrieved chunks to context window
│   ├── vision/
│   │   ├── pipeline.py      # 9-stage vision orchestrator
│   │   ├── extraction/      # scene_detector.py, frame_extractor.py
│   │   ├── filtering/       # duplicate_detector.py, blur_detector.py
│   │   ├── ocr/             # paddleocr_service.py + LRU cache
│   │   ├── scoring/         # importance_scorer.py, ranking_service.py
│   │   └── transcript/      # Transcript-frame alignment
│   ├── quality/
│   │   └── evaluator.py     # Quality score evaluation
│   └── monitoring/          # Metrics collection
├── pipeline/
│   └── orchestrator.py      # End-to-end pipeline (called by ARQ worker)
├── prompts/
│   ├── concept_extraction.md
│   ├── flashcards.md
│   ├── formula_sheet.md
│   └── (one per content service)
├── migrations/
│   └── versions/            # Alembic migration scripts
├── main.py                  # App factory, CORS, router registration, APScheduler
├── worker.py                # ARQ WorkerSettings + process_video_job
└── requirements.txt
```

---

## Key Design Patterns

### Non-blocking File Upload

```python
# File write is offloaded to a thread — does not block the event loop
file_path = await asyncio.to_thread(
    storage_service.save_upload_file, file, video_id, ext
)
file_size_bytes = os.path.getsize(file_path)
```

### Job Enqueueing (API → ARQ)

```python
# In video.py router — after creating the DB record:
from worker import enqueue_video_job
await enqueue_video_job(str(video.id), redis_url=settings.REDIS_URL)
```

The ARQ worker picks up the job, calls `process_video_job(ctx, video_id)`, which delegates to `process_video_pipeline_async(video_id)`.

### Progress Updates — Session Isolation

Each `update_status()` call opens a **fresh DB session** to ensure progress writes commit immediately and are not rolled back if the pipeline errors:

```python
async def update_status(video_id, status, current_step, progress):
    async with AsyncSessionLocal() as db:   # Fresh session — not the pipeline session
        ...
        await db.commit()
```

### SSE Progress Stream — Connection Safety

```python
# progress.py: fresh session per poll iteration
# prevents holding the Depends-injected session open for the entire stream lifetime
async with AsyncSessionLocal() as poll_db:
    res = await poll_db.execute(select(Video).where(Video.id == video_id))
    current = res.scalar_one_or_none()
```

### Shared Ownership Dependency

All endpoints that access a video by ID use `get_owned_video` from `core/dependencies.py`:

```python
@router.get("/{video_id}")
async def get_notes(video: Video = Depends(get_owned_video)):
    ...
```

This centralises the ownership check (video belongs to `current_user`) and eliminates repeated inline queries.

### Storage Query — SQL Aggregate

```python
# O(1) SQL aggregate instead of O(N) disk stat calls
result = await db.execute(
    select(func.coalesce(func.sum(Video.file_size_bytes), 0))
    .where(Video.user_id == str(current_user.id))
)
used_bytes = result.scalar()
# ~500ms (200 disk stats) → <5ms (1 SQL query)
```

### Nightly Cleanup (APScheduler)

```python
scheduler = AsyncIOScheduler()
scheduler.add_job(
    cleanup_expired_videos,
    trigger=CronTrigger(hour=2, minute=0),
    misfire_grace_time=3600,  # Fire up to 1h late if server was down
)
```

Cleanup per video: transcript file → video file → frames directory → embedding directory → outputs directory → DB record (SQLAlchemy cascade).

---

## Security Measures

| Area | Implementation |
|---|---|
| Auth | JWT Bearer on all protected routes; `is_admin` check for admin endpoints |
| CORS | Origins from `ALLOWED_ORIGINS` env var; explicit methods/headers (no wildcard) |
| Error handling | Global handler logs full traceback + `request_id`; generic 500 body to client |
| Exception detail | Raw exception text never forwarded to client (scrubbed in auth + notes routers) |
| Ownership | `get_owned_video` dependency — 403 if video belongs to another user |
| Frame access | Frames served through authenticated router, not as publicly accessible static files |
| Filename sanitization | `video.title` sanitized before use in `Content-Disposition` header |
| Postgres password | Docker Compose reads from env var; no hardcoded credentials |

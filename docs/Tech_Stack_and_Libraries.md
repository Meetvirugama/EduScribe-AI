# Tech Stack & Libraries

A full reference of every library used in EduScribe AI, with the reasoning for each choice.

---

## Frontend

| Library | Version | Purpose | Why chosen |
|---|---|---|---|
| React | 19 | UI framework | Concurrent rendering, rich ecosystem |
| Vite | 8 | Build tool + dev server | Fastest HMR, ESM-native |
| React Router | 7 | Client-side routing | Standard SPA routing |
| Lucide React | latest | SVG icon set | Lightweight, tree-shakeable |
| @tanstack/react-virtual | 3+ | Virtual list rendering | O(30) DOM nodes for 10k+ transcript segments |

**No Redux** — Context API is sufficient for the current 3 global state objects (auth, video list, workspace).

---

## Backend

### Web Framework

| Library | Purpose | Why chosen |
|---|---|---|
| FastAPI 0.110 | REST API | Async-first, auto OpenAPI docs, Pydantic validation |
| uvicorn | ASGI server | Production-grade, uvloop support |
| uvloop | Event loop | C-based replacement for Python asyncio (~2x throughput) |
| httpx | Async HTTP client | Used for Google OAuth2 token exchange |

### Database

| Library | Purpose |
|---|---|
| SQLAlchemy 2.0 (async) | ORM with AsyncPG driver |
| asyncpg | PostgreSQL async driver |
| Alembic | Schema migrations |
| psycopg2-binary | Sync fallback / Alembic migrations |

**Pool config:** `pool_size=10, max_overflow=20, pool_recycle=1800`

### Authentication

| Library | Purpose |
|---|---|
| python-jose / PyJWT | JWT creation and validation (HS256) |
| python-dotenv | Environment variable loading |
| pydantic-settings | Type-safe settings from `.env` |

### AI / ML

| Library | Version | Purpose | Notes |
|---|---|---|---|
| faster-whisper | 1.0+ | Speech-to-text | CTranslate2 backend, INT8, VAD, 4–8x faster than openai-whisper |
| ctranslate2 | 4.x | faster-whisper inference engine | INT8/INT4 quantized transformer inference |
| paddlepaddle | latest | OCR engine | PaddleOCR backend |
| paddleocr | latest | Text detection + recognition | slide/whiteboard optimized |
| opencv-python-headless | 4.x | Frame extraction, blur detection | headless (no GUI, Docker-safe) |
| imagehash | latest | Perceptual duplicate detection | dHash, 5–10x faster than pHash |
| rapidfuzz | latest | Fuzzy string matching | token_set_ratio transcript alignment |
| scenedetect | latest | Video scene boundary detection | ContentDetector + adaptive downscale |
| Pillow | latest | Image loading + draft() resize | Used for low-cost dHash decoding |
| numpy | latest | Frame matrix operations | Used by OpenCV and blur detection |

### Media Processing

| Library | Purpose |
|---|---|
| ffmpeg-python | Python wrapper for FFmpeg CLI |
| yt-dlp | YouTube video/audio downloader |
| youtube-transcript-api | YouTube native caption fetcher |

### Caching & Scheduling

| Library | Version | Purpose |
|---|---|---|
| cachetools | 5.5+ | LRUCache for OCR results (maxsize=500) |
| apscheduler | 3.10+ | Nightly expired video cleanup (AsyncIOScheduler) |

### Utilities

| Library | Purpose |
|---|---|
| aiofiles | Async file I/O helpers |
| python-multipart | FastAPI multipart form parsing |
| python-magic | (Recommended, not yet added) MIME type validation |

---

## Infrastructure

| Tool | Purpose |
|---|---|
| Docker | Container runtime |
| Docker Compose | Multi-service orchestration (PostgreSQL + Redis + backend + frontend) |
| PostgreSQL 15 | Relational database |
| Redis 7 | Declared in compose (for future Celery/cache use) |

---

## Dev Tools

| Tool | Purpose |
|---|---|
| Alembic | Database migration management |
| pytest / pytest-asyncio | Backend testing |
| Vite dev server | Frontend HMR |
| FastAPI `/docs` | Interactive Swagger UI |

---

## Dependency Notes

### faster-whisper vs openai-whisper

The project migrated from `openai-whisper` (PyTorch FP32) to `faster-whisper` (CTranslate2 INT8):

| Feature | openai-whisper | faster-whisper |
|---|---|---|
| Backend | PyTorch | CTranslate2 |
| Compute | FP32 | INT8 (configurable) |
| Speed (CPU) | Baseline | 4–8x faster |
| Memory | ~150MB (permanent) | ~75MB (freed after use) |
| VAD | No | Yes (`vad_filter=True`) |
| Streaming | No | Yes (segment generator) |

### dHash vs pHash

The project uses `imagehash.dhash()` not `imagehash.phash()`:

| Feature | dHash | pHash |
|---|---|---|
| Algorithm | Pixel gradient integer comparison | Discrete Cosine Transform (float) |
| Speed | 5–10x faster | Baseline |
| Accuracy (video dedup) | Equivalent | Equivalent |
| Memory per hash | 64 bits (integer) | 64 bits (float) |

### cachetools LRUCache vs Python dict

| Feature | dict | LRUCache(maxsize=500) |
|---|---|---|
| Memory growth | Unbounded | Capped at 500 entries |
| Eviction | None | Least-recently-used |
| Suitable for | Short sessions | Long videos (100s of frames) |

---

## requirements.txt (Backend)

Key packages (condensed):

```
fastapi==0.110.0
uvicorn[standard]
uvloop
sqlalchemy[asyncio]==2.0.*
asyncpg
alembic
psycopg2-binary
python-jose[cryptography]
pydantic-settings
httpx
faster-whisper>=1.0.3
ctranslate2
paddlepaddle
paddleocr
opencv-python-headless
imagehash
rapidfuzz
scenedetect
Pillow
numpy
ffmpeg-python
yt-dlp
youtube-transcript-api
apscheduler>=3.10.0
cachetools>=5.5.0
aiofiles
python-multipart
```

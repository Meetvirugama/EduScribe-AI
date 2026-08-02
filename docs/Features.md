# Features

A complete list of every implemented feature in EduScribe AI.

---

## 🔐 Authentication

| Feature | Status | Details |
|---|---|---|
| Google OAuth2 Login | ✅ | Google OAuth2 authorization code flow |
| JWT Session Management | ✅ | HS256, 24h expiry, stored in localStorage |
| Protected Routes | ✅ | `HTTPBearer` on all API endpoints |
| User Profile | ✅ | `/auth/me` returns email, name, picture |
| Auto-redirect on callback | ✅ | JWT passed via URL hash fragment to frontend |

---

## 📤 Content Intake

| Feature | Status | Details |
|---|---|---|
| File Upload | ✅ | MP4, MKV, MOV, AVI, MP3, WAV, M4A up to 1 GB |
| Non-blocking upload | ✅ | `asyncio.to_thread()` — event loop not blocked |
| YouTube URL ingestion | ✅ | Paste URL → automatic processing |
| YouTube metadata fetch | ✅ | Title, duration, thumbnail, channel via yt-dlp |
| YouTube native captions | ✅ | `youtube-transcript-api` (manual → auto-generated EN) |
| yt-dlp audio download | ✅ | Fallback if no captions available |
| Chrome cookie bypass | ✅ | Two-tier bot bypass (dev only) |
| Mid-stream size enforcement | ✅ | Rejects >1GB files without full buffering |
| File size tracking | ✅ | `file_size_bytes` stored in DB at upload time |

---

## 🎙️ Audio & Transcription

| Feature | Status | Details |
|---|---|---|
| FFmpeg audio extraction | ✅ | PCM 16-bit, 16kHz, mono, loudnorm, afftdn |
| FFmpeg multi-threading | ✅ | `--threads 4` (~50% faster) |
| faster-whisper INT8 | ✅ | CTranslate2 backend, 4–8x faster than openai-whisper |
| VAD filter | ✅ | Skips silence, ~20% additional speed gain |
| Auto language detection | ✅ | Whisper detects language automatically |
| Model lazy-load + lock | ✅ | Thread lock prevents duplicate model instances |
| Model unload after use | ✅ | Frees ~75MB RAM for OCR pipeline |
| Transcript JSON output | ✅ | Timestamped segments: `[{start, end, text}]` |
| Transcript TXT output | ✅ | Human-readable plaintext |
| YouTube captions priority | ✅ | Captions used if available, Whisper skipped |
| Word count analytics | ✅ | Stored in `transcripts.word_count` |

---

## 🎬 Vision Pipeline

| Feature | Status | Details |
|---|---|---|
| Scene detection | ✅ | PySceneDetect ContentDetector, threshold=27.0 |
| Adaptive downscaling | ✅ | `frame_width // 640` → 6x CPU reduction |
| Scene detection fallback | ✅ | Time-based segments for static content |
| Best-of-2 frame sampling | ✅ | Midpoint + 66% position, keep sharper |
| Blur scoring (Laplacian) | ✅ | CV_16S, 320px resize, pre-cached |
| Adaptive blur threshold | ✅ | `max(global_min, median * 0.5)` |
| dHash duplicate removal | ✅ | Hamming distance < 5, deque(maxlen=50) O(N) |
| PaddleOCR text extraction | ✅ | Lazy-load, asyncio lock, edge pre-filter |
| OCR LRU cache | ✅ | `cachetools.LRUCache(maxsize=500)` |
| OCR resize optimization | ✅ | Frames >1280px resized before inference |
| Transcript-frame matching | ✅ | RapidFuzz `token_set_ratio` |
| Per-scene frame scoring | ✅ | Composite score: blur + similarity + OCR |
| Per-scene best frame | ✅ | 1 best frame selected per scene (groupby fix) |
| Web-relative frame paths | ✅ | `storage/frames/{id}/scene_xxx.jpg` |
| Bulk DB insert | ✅ | Single transaction, no N+1 |
| Unselected frame cleanup | ✅ | Disk deletion of non-selected frames |

---

## 📊 Dashboard

| Feature | Status | Details |
|---|---|---|
| Video library grid | ✅ | All user videos with status indicators |
| Live progress tracking | ✅ | Percent + step name + ETA |
| Adaptive polling | ✅ | 3s when processing, 30s when idle |
| Analytics panel | ✅ | Total videos, total duration, total word count |
| Storage usage | ✅ | SQL SUM aggregate (O(1), <5ms) |
| Add Content modal | ✅ | Upload file or paste YouTube URL |
| Retention policy selector | ✅ | 7 / 14 / 30 days per video |
| Deep delete | ✅ | Cascade: DB + transcript + frames + notes + uploads |

---

## 🗂️ Workspace

| Feature | Status | Details |
|---|---|---|
| Metadata inspector | ✅ | Title, channel, duration, source, language |
| Transcript explorer | ✅ | Timestamped segments, searchable |
| Virtual scrolling | ✅ | `@tanstack/react-virtual` — O(30) DOM nodes |
| Key frames gallery | ✅ | Selected frames with thumbnail + timestamp |
| Frame OCR display | ✅ | Extracted text shown per frame card |
| Smart Merged Notes | ✅ | Markdown: transcript + frames + OCR inline |
| Notes download | ✅ | Download as `.md` file |

---

## 🏗️ Infrastructure

| Feature | Status | Details |
|---|---|---|
| DB connection pool | ✅ | pool_size=10, max_overflow=20, recycle=1800 |
| DB indexes | ✅ | videos(user_id), transcripts(video_id) |
| Nightly cleanup cron | ✅ | APScheduler 02:00 — deletes expired videos |
| Cascade delete | ✅ | SQLAlchemy `cascade="all, delete-orphan"` |
| Google OAuth2 | ✅ | Authorization code flow |
| Docker Compose | ✅ | PostgreSQL 15, Redis 7, backend, frontend |
| StaticFiles mount | ✅ | `/storage` served as static at `/storage` |

---

## 🔮 Planned Features (Future)

| Feature | Priority | Notes |
|---|---|---|
| httpOnly cookie auth | High | Replaces URL hash token |
| PKCE for OAuth2 | Medium | Authorization code protection |
| JWT expiry check (frontend) | Medium | Graceful logout before 401 |
| Rate limiting `/auth` | High | 5 req/min per IP (slowapi) |
| MIME type validation | High | python-magic for file uploads |
| Celery + Redis task queue | High | Retry, DLQ, concurrency control |
| Server-Sent Events progress | Medium | Replaces polling |
| S3/R2 object storage | Medium | Horizontal scaling |
| PaddleOCR GPU mode | Medium | 10x OCR speed |
| Parallel frame extraction | Medium | asyncio.Semaphore(4) across scenes |
| Redis-backed shared caches | Low | Survives server restart |
| faster-whisper large-v3-turbo | Low | Best CPU quality/speed |

# Features

All implemented features in EduScribe AI.

---

## 🔐 Authentication

| Feature | Status | Details |
|---|---|---|
| Google OAuth2 Login | ✅ | Authorization code flow |
| JWT Session Management | ✅ | HS256, 24h expiry, stored in localStorage |
| One-time code exchange | ✅ | `/auth/exchange` — prevents token in URL |
| Protected Routes (frontend) | ✅ | `ProtectedRoute` component redirects to `/login` |
| Protected Endpoints (backend) | ✅ | `HTTPBearer` + `get_current_user` dependency |
| User Profile | ✅ | `/auth/me` returns email, name, picture, is_admin |
| Admin RBAC | ✅ | `is_admin` column; `/admin` endpoints require it |

---

## 📤 Content Intake

| Feature | Status | Details |
|---|---|---|
| File Upload | ✅ | MP4, MKV, MOV, AVI, MP3, WAV, M4A — up to `MAX_VIDEO_SIZE_MB` (default 1 GB) |
| Non-blocking upload | ✅ | `asyncio.to_thread()` — event loop not blocked during large file writes |
| YouTube URL ingestion | ✅ | Paste URL → automatic processing |
| YouTube hostname validation | ✅ | Pydantic validator + service-level check; includes `music.youtube.com` |
| YouTube metadata fetch | ✅ | Title, duration, thumbnail, channel via yt-dlp (no download) |
| YouTube native captions | ✅ | `youtube-transcript-api` (manual EN → auto-generated EN fallback) |
| yt-dlp video download | ✅ | `bestvideo+bestaudio/mp4` format so OpenCV can process the file |
| Mid-stream size enforcement | ✅ | Rejects files exceeding limit without full buffering |
| File size tracking | ✅ | `file_size_bytes` stored in DB at upload for O(1) storage aggregate |
| Per-user rate limiting | ✅ | 5 uploads/hour; 10 YouTube/hour |

---

## 🎙️ Audio & Transcription

| Feature | Status | Details |
|---|---|---|
| FFmpeg audio extraction | ✅ | PCM 16-bit, 16kHz, mono; loudnorm + afftdn filters |
| FFmpeg multi-threading | ✅ | `--threads 4` (~50% faster filter graph) |
| faster-whisper INT8 | ✅ | CTranslate2 backend, 4–8× faster than openai-whisper |
| VAD filter | ✅ | Voice Activity Detection skips silence (~20% additional speed gain) |
| Auto language detection | ✅ | Whisper detects language automatically |
| Model lazy-load + lock | ✅ | Thread lock prevents duplicate model instances |
| Model unload after use | ✅ | Frees ~75 MB RAM for OCR pipeline |
| Transcript JSON output | ✅ | Timestamped segments: `[{start, end, text}]` |
| YouTube captions priority | ✅ | Captions used if available, Whisper skipped entirely |
| Word count analytics | ✅ | Stored in `transcripts.word_count` |

---

## 🎬 Vision Pipeline

| Feature | Status | Details |
|---|---|---|
| Scene detection | ✅ | PySceneDetect `ContentDetector`, threshold=27.0 |
| Adaptive downscaling | ✅ | `frame_width // 640` → ~6× CPU reduction |
| Scene detection fallback | ✅ | Time-based segments for static content |
| Best-of-2 frame sampling | ✅ | Midpoint + 66% position, keep sharper |
| Blur scoring (Laplacian) | ✅ | `CV_16S`, 320px resize, score cached from extraction |
| Adaptive blur threshold | ✅ | `max(global_min, median × 0.5)` — prevents over-filtering dark content |
| dHash duplicate removal | ✅ | Hamming distance < 5; `deque(maxlen=50)` O(N) |
| OCR text pre-filter | ✅ | Edge density check skips ~40% of frames with no text |
| PaddleOCR text extraction | ✅ | Async lock, LRU cache 500 entries, resize to ≤1280px |
| Transcript-frame matching | ✅ | RapidFuzz `token_set_ratio` |
| Per-scene frame scoring | ✅ | Composite: blur + similarity + OCR line count + confidence |
| Per-scene best frame | ✅ | 1 best frame selected per scene via `itertools.groupby` |
| Bulk DB insert | ✅ | Single transaction; no N+1 |
| Unselected frame cleanup | ✅ | Disk deletion of non-selected frames |
| Authenticated frame serving | ✅ | Frames served through `/frames/video/{id}/image/{frame_id}` with Bearer auth |

---

## 🧠 LLM Content Generation

| Feature | Status | Details |
|---|---|---|
| Multi-provider LLM | ✅ | Gemini, Groq, OpenRouter, Cohere, Cloudflare, HuggingFace via litellm |
| Multi-key rotation | ✅ | Round-robin across comma-separated keys per provider |
| Quota tracking | ✅ | Tracks usage; skips exhausted providers automatically |
| Automatic retry | ✅ | Exponential back-off × 3 attempts per service |
| Fallback chain | ✅ | Falls back through provider chain on persistent failure |
| Response validation | ✅ | Pydantic schema validation + JSON repair |
| Concept extraction | ✅ | Key concept list from transcript |
| Quiz generation | ✅ | Multiple-choice + short-answer questions |
| Flashcard generation | ✅ | Q&A flashcard pairs |
| Mind map generation | ✅ | JSON mind map structure |
| Formula sheet | ✅ | LaTeX-formatted formulas |
| Interview prep | ✅ | Interview Q&A |
| Revision plan | ✅ | Structured revision schedule |
| Parallel LLM phases | ✅ | `asyncio.gather` across independent tasks (~75s → ~20s) |
| Prompt templates | ✅ | Jinja2 templates in `backend/prompts/` per service |

---

## 🔍 RAG Search

| Feature | Status | Details |
|---|---|---|
| Transcript chunking | ✅ | 4 strategies: `token`, `semantic`, `timestamp`, `topic` |
| Structure detection | ✅ | Classifies chunks: equation, code, definition, narrative, etc. |
| Embedding indexing | ✅ | Jina AI embeddings stored to `storage/embeddings/{video_id}/` |
| Hybrid retrieval | ✅ | BM25 + dense vectors, `HYBRID_BM25_ALPHA=0.5` |
| MMR re-ranking | ✅ | Balances relevance vs. diversity, `MMR_LAMBDA=0.7` |
| Semantic search endpoint | ✅ | `GET /notes/{video_id}/search?query=...` |

---

## 📊 Dashboard

| Feature | Status | Details |
|---|---|---|
| Video library grid | ✅ | All user videos with status indicators |
| SSE real-time progress | ✅ | `GET /videos/{id}/progress/stream` — server-sent events |
| Analytics panel | ✅ | Total videos, total duration, total word count |
| Storage usage | ✅ | SQL SUM aggregate (O(1), <5ms) |
| Add Content modal | ✅ | Upload file or paste YouTube URL |
| Retention policy selector | ✅ | 7 / 14 / 30 days per video (max 30) |
| Deep delete | ✅ | Cascade: DB + transcript + frames + notes + embeddings |

---

## 🗂️ Workspace

| Feature | Status | Details |
|---|---|---|
| Metadata inspector | ✅ | Title, channel, duration, source, language |
| Transcript explorer | ✅ | Timestamped segments, searchable |
| Virtual scrolling | ✅ | `@tanstack/react-virtual` — ~30 DOM nodes regardless of length |
| Key frames gallery | ✅ | Selected frames with thumbnail + timestamp |
| Frame OCR display | ✅ | Extracted text shown per frame card |
| Smart Merged Notes | ✅ | Markdown: transcript + frames + OCR inline |
| Notes search | ✅ | Semantic search over indexed transcript |
| Notes download | ✅ | Download as `.md` file |

---

## 🏗️ Infrastructure

| Feature | Status | Details |
|---|---|---|
| DB connection pool | ✅ | pool_size=10, max_overflow=20, pool_recycle=1800 |
| DB indexes | ✅ | `videos(user_id)`, `transcripts(video_id)` |
| ARQ job queue | ✅ | Redis-backed; retry, persistence, deduplication |
| Nightly cleanup cron | ✅ | APScheduler 02:00 UTC — cascade-deletes expired videos + all artifacts |
| SQLAlchemy cascade delete | ✅ | `cascade="all, delete-orphan"` on all child tables |
| CORS hardening | ✅ | Origins from env var; explicit methods/headers only |
| Global exception handler | ✅ | Logs `request_id`, never leaks internals to client |
| SSE connection management | ✅ | Fresh DB session per poll — no connection pool exhaustion |
| Docker Compose | ✅ | PostgreSQL 15, Redis 7, backend, ARQ worker, frontend |
| Postgres credentials | ✅ | From env vars; no hardcoded password in compose file |

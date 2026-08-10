# Configuration Reference

All configuration is loaded from `backend/.env` by `core/config.py` using `pydantic-settings`. Copy `backend/.env.example` to `backend/.env` and fill in your values.

---

## Minimal Required Variables

These variables **must** be set — the application will not start without them:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/eduscribe
JWT_SECRET=your-random-64-char-jwt-signing-key
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
```

Plus at least one LLM provider key (see LLM Keys section below).

---

## Full Reference

### Database

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | *(required)* | PostgreSQL async connection string. Must use `postgresql+asyncpg://` scheme. `sslmode` parameter is automatically stripped. |

**Example:**
```env
# Local Docker
DATABASE_URL=postgresql+asyncpg://admin:password@localhost:5432/eduscribe

# Neon serverless
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.us-east-1.aws.neon.tech/eduscribe
```

---

### Authentication

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET` | *(required)* | JWT signing key. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime in minutes (default = 24 hours) |
| `GOOGLE_CLIENT_ID` | *(required)* | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | *(required)* | From Google Cloud Console |

---

### URLs

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `http://localhost:5001` | Backend URL (used to build OAuth callback URI) |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend URL (used for post-login redirect) |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated CORS allowed origins |

---

### Storage

All paths are relative to the backend working directory.

| Variable | Default | Description |
|---|---|---|
| `UPLOAD_DIR` | `storage/uploads` | Incoming video files (deleted after pipeline) |
| `OUTPUT_DIR` | `storage/outputs` | Merged Markdown notes |
| `TEMP_DIR` | `storage/temp` | Temporary WAV audio files |
| `TRANSCRIPT_DIR` | `storage/transcripts` | Transcript JSON + TXT files |
| `FRAMES_DIR` | `storage/frames` | Extracted JPEG keyframes |
| `EMBEDDING_DIR` | `storage/embeddings` | RAG vector index per video |
| `METRICS_DIR` | `storage/metrics` | Quality evaluation metrics |

All directories are **created automatically** on backend startup.

---

### Redis (ARQ Job Queue)

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `None` | Redis connection string. Required to run the ARQ worker. Example: `redis://localhost:6379/0` |

> **Note:** If `REDIS_URL` is not set, the ARQ worker cannot start. The API can still run, but video processing jobs will not execute.

---

### Retention Policy

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_RETENTION_DAYS` | `7` | Default retention for new videos |
| `MAX_RETENTION_DAYS` | `30` | Maximum retention a user can request (matches frontend "30 Days (Maximum)") |

---

### Upload Limits

| Variable | Default | Description |
|---|---|---|
| `MAX_VIDEO_SIZE_MB` | `1024` | Maximum upload file size in megabytes |
| `SUPPORTED_VIDEO_FORMATS` | `mp4,mkv,mov,avi` | Accepted video extensions |
| `SUPPORTED_AUDIO_FORMATS` | `mp3,wav,m4a` | Accepted audio extensions |
| `MAX_VIDEO_DURATION_SECONDS` | `7200` | Max video length (2 hours) |
| `MAX_UPLOADS_PER_HOUR` | `5` | Per-user rate limit for file uploads |
| `MAX_YOUTUBE_PER_HOUR` | `10` | Per-user rate limit for YouTube ingestion |

---

### Whisper

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `base` | Model size: `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo` |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` (requires CUDA 11.x + cuDNN 8.x) |

**Model selection guide:**

| Model | Parameters | CPU Time (1hr audio) | VRAM (GPU) |
|---|---|---|---|
| `tiny` | 39M | ~1–2 min | 0.5 GB |
| `base` | 74M | ~3–4 min ✅ default | 1 GB |
| `small` | 244M | ~8–10 min | 2 GB |
| `medium` | 769M | ~20–25 min | 5 GB |
| `large-v3` | 1.5B | ~60–90 min | 10 GB |
| `large-v3-turbo` | distilled | ~15–20 min | 6 GB |

For GPU production: `large-v3-turbo` with `WHISPER_DEVICE=cuda` gives the best quality/cost ratio.

---

### Vision Pipeline Tuning

| Variable | Default | Description |
|---|---|---|
| `SCENE_DETECT_THRESHOLD` | `27.0` | PySceneDetect sensitivity (lower = more scenes detected) |
| `SCENE_MIN_LEN_FRAMES` | `15` | Minimum frames per detected scene |
| `BLUR_THRESHOLD` | `30.0` | Laplacian variance minimum (adaptive threshold overrides this per-video) |
| `PHASH_THRESHOLD` | `5` | dHash Hamming distance threshold for duplicate detection |
| `OCR_MIN_CONFIDENCE` | `0.70` | Minimum PaddleOCR confidence to accept a text detection |
| `TRANSCRIPT_MATCH_MIN_SCORE` | `10.0` | Minimum RapidFuzz score to record a frame-transcript match |

**Threshold guidance:**

| `SCENE_DETECT_THRESHOLD` | Effect |
|---|---|
| 15–20 | Very sensitive — many small scenes; use for fast-cut video |
| **27.0** | ✅ Recommended — balanced for slide-based lectures |
| 35–50 | Lenient — may miss subtle slide transitions |

| `PHASH_THRESHOLD` | Effect |
|---|---|
| 2–3 | Strict — only near-identical frames removed |
| **5** | ✅ Default — ~8% pixel difference tolerance |
| 8–10 | Lenient — use for compressed or low-quality streams |

---

### RAG Configuration

| Variable | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `1000` | Target chunk size in characters |
| `CHUNK_OVERLAP` | `200` | Overlap between adjacent chunks |
| `TOP_K_RESULTS` | `5` | Number of chunks to retrieve before re-ranking |
| `CHUNK_STRATEGY` | `timestamp` | Chunking strategy: `token`, `semantic`, `timestamp`, `topic` |
| `MMR_LAMBDA` | `0.7` | MMR relevance weight (0 = max diversity, 1 = max relevance) |
| `HYBRID_BM25_ALPHA` | `0.5` | BM25 weight in hybrid retrieval (0 = dense only, 1 = BM25 only) |
| `EMBED_MODEL_VERSION` | `v1` | Bump to force re-embedding of all videos |
| `RERANK_TOP_N` | `3` | Final results returned after MMR re-ranking |

---

### LLM API Keys

Multiple keys per provider are supported (comma-separated). The key manager round-robins across them.

```env
# Google Gemini (https://aistudio.google.com)
GEMINI_API_KEYS=your-key-1,your-key-2

# Groq (https://console.groq.com)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

# OpenRouter (https://openrouter.ai)
OPENROUTER_API_KEYS=sk-or-v1-key1,sk-or-v1-key2

# Cohere (https://dashboard.cohere.com)
COHERE_API_KEYS=your-cohere-key-1

# Cloudflare AI (https://dash.cloudflare.com)
# Cloudflare requires Account ID paired with API Key — use numbered format:
CLOUDFLARE_ACCOUNT_ID_1=your-account-id-1
CLOUDFLARE_API_KEY_1=your-api-key-1
CLOUDFLARE_ACCOUNT_ID_2=your-account-id-2
CLOUDFLARE_API_KEY_2=your-api-key-2

# HuggingFace (https://huggingface.co/settings/tokens)
HUGGINGFACE_API_KEYS=hf_key1,hf_key2

# Jina AI — used for RAG embeddings (https://jina.ai/api-key)
JINA_API_KEY=jina_your-key
```

---

### Quality Evaluation

| Variable | Default | Description |
|---|---|---|
| `MIN_QUALITY_SCORE` | `0.5` | Minimum composite quality score — below this triggers a warning log |

---

## Docker Compose Environment

When running with Docker Compose, set these in a `.env` file at the project root (or in `docker-compose.yml`). Use **service names** as hostnames:

```env
DATABASE_URL=postgresql+asyncpg://admin:password@postgres:5432/eduscribe
REDIS_URL=redis://redis:6379/0
BASE_URL=http://localhost:5001
FRONTEND_URL=http://localhost:5173
```

The PostgreSQL container credentials are also controlled by env vars:
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=your-strong-password   # set in .env, never commit
POSTGRES_DB=eduscribe
```

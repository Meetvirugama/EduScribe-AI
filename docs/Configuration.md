# Configuration Reference

EduScribe AI is configured via environment variables in `backend/.env`. All settings are loaded by `core/config.py` using `pydantic-settings`.

---

## Full `.env` Reference

```env
# ─────────────────────────────────────
# Database
# ─────────────────────────────────────

# PostgreSQL async connection string (asyncpg driver)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/eduscribe

# ─────────────────────────────────────
# Security
# ─────────────────────────────────────

# JWT signing secret — use a random 64-char string in production
SECRET_KEY=change-this-to-a-random-64-char-string

# JWT algorithm (HS256 is the current default)
ALGORITHM=HS256

# JWT token expiry in minutes (default: 1440 = 24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ─────────────────────────────────────
# Google OAuth2
# ─────────────────────────────────────

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Where the frontend is running (used for post-login redirect)
FRONTEND_URL=http://localhost:5173

# Where the backend is running (used to construct OAuth callback URL)
BACKEND_URL=http://localhost:5001

# ─────────────────────────────────────
# Storage
# ─────────────────────────────────────

# Root of all file storage (relative to backend working directory)
STORAGE_DIR=../storage
UPLOAD_DIR=../storage/uploads
TEMP_DIR=../storage/temp
TRANSCRIPT_DIR=../storage/transcripts
FRAMES_DIR=../storage/frames
OUTPUT_DIR=../storage/outputs

# ─────────────────────────────────────
# Upload Limits
# ─────────────────────────────────────

MAX_VIDEO_SIZE_MB=1024

# ─────────────────────────────────────
# faster-whisper
# ─────────────────────────────────────

# Model size: tiny | base | small | medium | large-v3 | large-v3-turbo
# Default: base (best CPU tradeoff)
WHISPER_MODEL=base

# Device: cpu | cuda
# For GPU: requires CUDA 11.x + cuDNN 8.x
WHISPER_DEVICE=cpu

# ─────────────────────────────────────
# Vision Pipeline
# ─────────────────────────────────────

# PySceneDetect: content change threshold (lower = more sensitive)
# 27.0 recommended for lecture recordings
SCENE_DETECT_THRESHOLD=27.0

# PySceneDetect: minimum scene length in frames
SCENE_MIN_LEN_FRAMES=15

# Laplacian variance blur cutoff (adaptive threshold overrides this at runtime)
BLUR_THRESHOLD=100.0

# Hamming distance threshold for dHash duplicate detection
PHASH_THRESHOLD=5

# PaddleOCR confidence filter (0.0–1.0)
OCR_MIN_CONFIDENCE=0.70

# PaddleOCR language
OCR_LANG=en

# Minimum RapidFuzz similarity to record a transcript match
TRANSCRIPT_MATCH_MIN_SCORE=10.0

# ─────────────────────────────────────
# Retention
# ─────────────────────────────────────

# Default retention days if user doesn't specify (7, 14, or 30)
DEFAULT_RETENTION_DAYS=7
```

---

## Settings Object (`core/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:5001"

    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"

    SCENE_DETECT_THRESHOLD: float = 27.0
    BLUR_THRESHOLD: float = 100.0
    PHASH_THRESHOLD: int = 5
    OCR_MIN_CONFIDENCE: float = 0.70
    MAX_VIDEO_SIZE_MB: int = 1024

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Whisper Model Selection Guide

| Model | Size | CPU Speed (1hr audio) | Accuracy | VRAM (GPU) |
|---|---|---|---|---|
| `tiny` | 39M params | ~1–2 min | Good | 0.5 GB |
| `base` | 74M params | ~3–4 min ✅ default | Very good | 1 GB |
| `small` | 244M params | ~8–10 min | Great | 2 GB |
| `medium` | 769M params | ~20–25 min | Excellent | 5 GB |
| `large-v3` | 1.5B params | ~60–90 min | Best | 10 GB |
| `large-v3-turbo` | distilled | ~15–20 min | Near-best | 6 GB |

For production with GPU: `large-v3-turbo` with `compute_type="int8_float16"` gives the best quality/cost ratio.

---

## Vision Threshold Tuning

### `SCENE_DETECT_THRESHOLD`

| Value | Effect |
|---|---|
| 15–20 | Very sensitive — catches minor camera moves, produces many small scenes |
| **27.0** | ✅ Recommended — good balance for slide-based lectures |
| 35–50 | Lenient — may miss subtle slide transitions |

### `BLUR_THRESHOLD`

The adaptive threshold (`max(BLUR_THRESHOLD, median_score * 0.5)`) overrides this at runtime for each video. Lower this value if too many frames are being discarded for dark/low-contrast content.

| Value | Effect |
|---|---|
| 30–50 | Keep most frames (use for webcam/whiteboard content) |
| **100.0** | ✅ Default (adaptive threshold adjusts automatically) |
| 150–200 | Strict (only very sharp frames kept) |

### `PHASH_THRESHOLD` (dHash Hamming distance)

| Value | Effect |
|---|---|
| 2–3 | Strict — only near-identical frames removed |
| **5** | ✅ Default — ~8% pixel difference tolerance |
| 8–10 | Lenient — use for heavily compressed or low-quality streams |

---

## Docker Compose Environment

When using Docker Compose, environment variables can be set in `docker-compose.yml` or via a `.env` file at the project root:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/eduscribe
      - SECRET_KEY=your-secret-key
      - GOOGLE_CLIENT_ID=your-client-id
      - GOOGLE_CLIENT_SECRET=your-client-secret
      - FRONTEND_URL=http://localhost:5173
```

Note: When running in Docker, use the **service name** (`postgres`) as the DB host, not `localhost`.

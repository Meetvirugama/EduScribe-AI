# Deployment Guide

This guide covers local development and Docker-based deployment for EduScribe AI.

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.9+ | Backend |
| Node.js | 18+ | Frontend |
| PostgreSQL | 15 | Database |
| Redis | 7 | ARQ job queue |
| Docker + Compose | latest | Full containerised setup |
| FFmpeg | 4.x+ | Audio extraction (system-level) |
| git | any | Clone the repo |

---

## Google OAuth2 Setup

Before running either locally or via Docker, you need a Google OAuth2 app.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google People API**
3. **Credentials** → **Create OAuth 2.0 Client ID** → Web application
4. Set **Authorized redirect URIs:**
   - Local dev: `http://localhost:5001/auth/google/callback`
   - Production: `https://api.yourdomain.com/auth/google/callback`
5. Copy the **Client ID** and **Client Secret** into `backend/.env`

---

## Local Development (No Docker)

### 1. Clone

```bash
git clone https://github.com/Meetvirugama/EduScribe-AI.git
cd EduScribe-AI
```

### 2. Environment Variables

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum set:
#   DATABASE_URL, JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
#   REDIS_URL (if you want the ARQ worker to run)
#   At least one LLM provider key (GEMINI_API_KEYS, GROQ_API_KEYS, etc.)
```

### 3. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate           # macOS/Linux
# or:  venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

**Install FFmpeg (system-level):**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 4. Database

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE eduscribe;"

# Run Alembic migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

### 5. Run the API Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

- API: `http://localhost:5001`
- Swagger docs: `http://localhost:5001/docs`

### 6. Run the ARQ Worker (separate terminal)

```bash
cd backend
source venv/bin/activate
arq worker.WorkerSettings
```

> **Important:** The API server and ARQ worker must both be running for video processing to work. The API enqueues jobs in Redis; the worker dequeues and executes them.

### 7. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

---

## Docker Compose (Recommended)

Starts PostgreSQL, Redis, the FastAPI backend, the ARQ worker, and the Vite frontend with a single command.

### 1. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env using Docker service names as hosts:
#   DATABASE_URL=postgresql+asyncpg://admin:password@postgres:5432/eduscribe
#   REDIS_URL=redis://redis:6379/0
```

### 2. Start All Services

```bash
docker compose up --build -d
```

Services started:
- **postgres** → `localhost:5432`
- **redis** → `localhost:6379`
- **backend** (FastAPI + uvicorn) → `http://localhost:5001`
- **worker** (ARQ) — background job processor
- **frontend** (Vite dev server) → `http://localhost:5173`

### 3. Run Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Useful Commands

```bash
# View logs for all services
docker compose logs -f

# View only worker logs
docker compose logs -f worker

# Restart a single service
docker compose restart backend

# Stop without losing data
docker compose down

# Stop and delete volumes (wipes database)
docker compose down -v
```

---

## Storage Volumes

The backend creates these directories on startup (relative to working directory):

| Directory | Contents | Deleted When |
|---|---|---|
| `storage/uploads/` | Incoming video files | After pipeline completes |
| `storage/temp/` | Audio WAV files | In pipeline `finally` block |
| `storage/transcripts/` | JSON + TXT transcripts | At `expires_at` (nightly cron) |
| `storage/frames/{video_id}/` | Selected JPEG keyframes | At `expires_at` |
| `storage/outputs/{video_id}/` | Merged Markdown notes | At `expires_at` |
| `storage/embeddings/{video_id}/` | RAG vector index | At `expires_at` |

For production, mount these directories as persistent Docker volumes:

```yaml
volumes:
  - ./storage:/app/storage
```

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View full migration history
alembic history

# Create a new auto-generated migration
alembic revision --autogenerate -m "add my new column"

# Roll back one migration
alembic downgrade -1
```

**Applied migrations:**
- `8a92f814b3d2` — Initial schema (users, videos, transcripts, video_frames, etc.)
- `63c689249d08` — Added DB indexes + `file_size_bytes` column

---

## Production Checklist

**Security:**
- [ ] Set `JWT_SECRET` to a cryptographically random 64-char string
- [ ] Set `ALLOWED_ORIGINS` to only your production domain (not localhost)
- [ ] Use a strong `POSTGRES_PASSWORD` in `.env` (never the Docker default)
- [ ] Add Nginx reverse proxy with SSL (Let's Encrypt)
- [ ] Disable Swagger UI in production (`app = FastAPI(docs_url=None, redoc_url=None)`)

**Infrastructure:**
- [ ] Mount persistent Docker volumes for `storage/`
- [ ] Configure PostgreSQL backups (pg_dump cron or managed service)
- [ ] Set `REDIS_URL` to a persistent Redis instance (not ephemeral)
- [ ] Confirm the ARQ worker container is running and healthy

**Performance:**
- [ ] Set `WHISPER_MODEL=large-v3-turbo` and `WHISPER_DEVICE=cuda` if GPU available
- [ ] Consider PaddleOCR GPU mode (~10× faster OCR)
- [ ] Set `MAX_VIDEO_SIZE_MB` and `MAX_VIDEO_DURATION_SECONDS` to appropriate production limits

---

## Troubleshooting

### Backend fails to start

Check that all required env vars are set:
```bash
cd backend && python3 -c "from core.config import settings; print('OK')"
```

### ARQ worker not processing jobs

```bash
# Check Redis is reachable
redis-cli -u $REDIS_URL ping

# Check worker logs
docker compose logs -f worker

# Manually inspect queued jobs
arq info worker.WorkerSettings
```

### PaddleOCR model download on first run

PaddleOCR downloads model weights (~200 MB) on first use. Ensure internet access on first boot. Weights are cached at `~/.paddleocr/`.

PaddleOCR has complex platform/GPU-specific install requirements. If not installed, the OCR stage is gracefully skipped (a runtime `ImportError` guard is in place). Install manually:
```bash
pip install paddlepaddle paddleocr
```

### Video stuck in PROCESSING

```bash
# Check orchestrator logs in the worker
docker compose logs worker | grep "video_id"

# Manually reset stuck videos (use with care)
psql $DATABASE_URL -c "
  UPDATE videos
  SET status='FAILED', error_message='Manually reset'
  WHERE status NOT IN ('COMPLETED','FAILED')
    AND processing_started_at < NOW() - INTERVAL '2 hours';
"
```

### `yt-dlp` "Sign in to confirm you're not a bot"

```bash
# Update yt-dlp
pip install -U yt-dlp
```

If the issue persists, export cookies from a logged-in Chrome session and mount `cookies.txt` in the container.

### Database connection refused

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify DATABASE_URL in .env
grep DATABASE_URL backend/.env
```

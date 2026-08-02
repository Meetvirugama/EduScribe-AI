# Deployment Guide

This guide covers local development setup and Docker-based deployment for EduScribe AI.

---

## Prerequisites

| Tool | Minimum Version | Required For |
|---|---|---|
| Python | 3.9+ | Backend |
| Node.js | 18+ | Frontend |
| PostgreSQL | 15 | Database |
| Docker + Compose | latest | Full containerized setup |
| FFmpeg | 4.x+ | Audio extraction (system-level) |

---

## Local Development (No Docker)

### 1. Clone the Repository

```bash
git clone https://github.com/Meetvirugama/EduScribe-AI.git
cd EduScribe-AI
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate       # macOS/Linux
# or: venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

**Install FFmpeg (system-level):**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 3. Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/eduscribe
SECRET_KEY=your-super-secret-jwt-key-change-in-production
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:5001

# Optional
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
MAX_VIDEO_SIZE_MB=1024
```

### 4. Database Setup

```bash
# Create database
psql -U postgres -c "CREATE DATABASE eduscribe;"

# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

### 5. Run the Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

API available at: `http://localhost:5001`
Swagger docs: `http://localhost:5001/docs`

### 6. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## Docker Compose (Recommended)

The Docker Compose setup starts all services (PostgreSQL, Redis, backend, frontend) with a single command.

### 1. Configure Environment

Create `backend/.env` as above (but use Docker service names for hosts):

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/eduscribe
```

### 2. Start All Services

```bash
docker compose up --build
```

Services started:
- **PostgreSQL 15** → `localhost:5432`
- **Redis 7** → `localhost:6379`
- **Backend (FastAPI)** → `http://localhost:5001`
- **Frontend (Vite)** → `http://localhost:5173`

### 3. Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Stop Services

```bash
docker compose down          # Stop without deleting data
docker compose down -v       # Stop and delete database volumes
```

---

## Storage Directories

The backend automatically creates these directories on startup:

| Directory | Contents |
|---|---|
| `backend/storage/uploads/` | Uploaded video files (deleted after pipeline) |
| `backend/storage/temp/` | Audio WAV files (deleted after transcription) |
| `backend/storage/transcripts/` | Transcript JSON + TXT files |
| `backend/storage/frames/` | Extracted JPEG keyframes (per video_id subdirectory) |
| `backend/storage/outputs/` | Smart Notes Markdown files |

**Important:** Frame images are served by FastAPI's `StaticFiles` mount at `/storage`. The frontend constructs frame URLs as:
```
http://localhost:5001/storage/frames/{video_id}/scene_xxxx.jpg
```

---

## Google OAuth2 Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google+ API** and **People API**
3. Go to **Credentials** → **Create OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Authorized redirect URIs:
   - `http://localhost:5001/auth/google/callback`
6. Copy **Client ID** and **Client Secret** → paste into `backend/.env`

---

## Running Migrations

All Alembic migrations are in `backend/migrations/versions/`.

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history

# Create a new migration
alembic revision --autogenerate -m "description"
```

**Applied migrations:**
- `8a92f814b3d2` — Initial schema (users, videos, transcripts, video_frames, etc.)
- `63c689249d08` — Added DB indexes (`videos.user_id`, `transcripts.video_id`) + `file_size_bytes` column

---

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a cryptographically random 64-char string
- [ ] Set `DEBUG=false` in environment
- [ ] Configure real PostgreSQL credentials
- [ ] Set up Nginx reverse proxy with SSL (Let's Encrypt)
- [ ] Add `ALLOWED_ORIGINS` to only include your domain
- [ ] Set up persistent Docker volumes for `/storage/`
- [ ] Configure backup for PostgreSQL
- [ ] Monitor APScheduler nightly cleanup logs

**Security hardening (recommended):**
- [ ] Add rate limiting to `/auth` endpoints (5 req/min per IP)
- [ ] Validate MIME types on upload (python-magic)
- [ ] Switch from URL hash token to httpOnly cookie

---

## Troubleshooting

### `faster-whisper` fails to load

```bash
# Ensure ctranslate2 and faster-whisper are installed
pip install "faster-whisper>=1.0.3"

# Check Python version compatibility (requires Python 3.9+)
python --version
```

### PaddleOCR download on first run

PaddleOCR downloads model weights on first use (~200MB). Ensure internet access on first boot. Models are cached at `~/.paddleocr/`.

### Database connection refused

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check DATABASE_URL in .env
echo $DATABASE_URL
```

### Frames not showing in frontend

Frame paths must be web-relative (`storage/frames/...`). If you see 404 errors:

1. Check that `StaticFiles` is mounted in `main.py`:
   ```python
   app.mount("/storage", StaticFiles(directory="storage"), name="storage")
   ```
2. Verify frame files exist in the correct directory.
3. Check that `frame_path` in DB is web-relative, not absolute.

### Video stuck in PROCESSING

1. Check backend logs for pipeline errors.
2. The nightly APScheduler cron does **not** clean up failed videos (only expired ones).
3. Manually update status if needed:
   ```sql
   UPDATE videos SET status='FAILED' WHERE status='PROCESSING' AND updated_at < NOW() - INTERVAL '2 hours';
   ```

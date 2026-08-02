# Troubleshooting Guide

Common issues and their fixes when developing or deploying EduScribe AI.

---

## Audio & Transcription

### `faster-whisper` fails to load / `ModuleNotFoundError`

**Symptom:** Backend crashes with `ModuleNotFoundError: No module named 'faster_whisper'`

**Fix:**
```bash
cd backend
source venv/bin/activate
pip install "faster-whisper>=1.0.3"
```

---

### Transcription is slow (>10 min for 1-hour lecture)

**Cause:** Running `openai-whisper` instead of `faster-whisper`, or model not quantized.

**Check:** The current implementation uses `faster-whisper` with `compute_type="int8"`. Confirm in `services/whisper_service.py`:
```python
model = WhisperModel("base", device="cpu", compute_type="int8")
```

**Expected speed:** ~3–4 min for 1-hour audio on CPU.

---

### `yt-dlp` "Sign in to confirm you're not a bot"

**Symptom:** YouTube URL fails immediately with a bot-protection error.

**Cause:** YouTube updates anti-bot algorithms frequently, blocking yt-dlp requests from unknown IPs.

**Fix:**
1. Update yt-dlp: `pip install -U yt-dlp`
2. If issue persists, mount a `cookies.txt` file (exported from a logged-in Chrome session) into the Docker container and set the path in `youtube_service.py`.

> **Note:** Chrome cookie bypass works in local development but Chrome is not available in Docker containers.

---

### FFmpeg not found

**Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Fix:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Verify
ffmpeg -version
```

---

## Vision Pipeline

### Gallery shows 0 selected frames

**Symptom:** The Key Frames Gallery in the Workspace is empty even after processing completes.

**Cause (now fixed):** The old `ranking_service.py` applied `top_n=1` globally — selecting only 1 frame for the entire video. This was fixed with per-scene groupby selection.

**Verify the fix is applied:**
```python
# backend/services/vision/scoring/ranking_service.py
# Should use itertools.groupby, NOT a global sort + slice
from itertools import groupby
for scene_num, scene_iter in groupby(scored_frames, key=lambda x: x["scene_number"]):
    ...
```

If you see only 1 frame in the gallery, check that the latest code is deployed.

---

### Frame images return 404

**Symptom:** Frame thumbnails fail to load in the gallery; browser shows `GET /storage/frames/... 404`.

**Cause 1 — Wrong frame path in DB:** Old versions stored absolute OS paths (e.g. `/Users/meet/Desktop/.../storage/frames/...`). Current code stores web-relative paths (`storage/frames/{video_id}/scene_xxxx.jpg`).

**Fix:** Check a frame record in the DB:
```sql
SELECT frame_path FROM video_frames LIMIT 5;
```
Paths must start with `storage/`, not `/Users/` or `/home/`.

**Cause 2 — StaticFiles not mounted:** Ensure `main.py` has:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
```

**Cause 3 — Files deleted:** Unselected frames are deleted during cleanup. Only `is_selected=True` frames are retained on disk.

---

### All frames are blurry (gallery empty after processing)

**Symptom:** Pipeline completes but `blur_filter` discards all frames.

**Fix:** Lower the blur threshold. The adaptive threshold `max(BLUR_THRESHOLD, median * 0.5)` adjusts automatically, but the global minimum (`BLUR_THRESHOLD`) may be too high for webcam/whiteboard content.

```env
# backend/.env — lower from 100.0 to 50.0 for webcam/dark content
BLUR_THRESHOLD=50.0
```

---

### Scene detection finds 0 scenes (static content)

**Symptom:** Log shows `0 scenes detected`, pipeline uses fallback.

**Cause:** `ContentDetector` threshold too high for the content, or the video has very slow transitions.

**Fix:** Lower `SCENE_DETECT_THRESHOLD`:
```env
SCENE_DETECT_THRESHOLD=15.0   # More sensitive
```

The fallback automatically creates time-based segments if 0 scenes are detected — the pipeline won't abort.

---

### PaddleOCR download hangs on first run

**Cause:** PaddleOCR downloads model weights (~200–500MB) on first use.

**Fix:** Ensure internet access during first startup. Models cache at `~/.paddleocr/`. Pre-warm in Docker startup:
```bash
docker compose exec backend python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='en')"
```

---

## Database

### Neon PostgreSQL connection drops mid-pipeline

**Symptom:** Background task crashes with `asyncpg.exceptions.ConnectionDoesNotExistError` after long Whisper transcription.

**Cause:** Neon serverless PostgreSQL aggressively drops idle connections. The vision pipeline uses a session that may have been idle for 5–15 minutes during Whisper processing.

**Fix (already applied):** `pool_recycle=1800` in `core/database.py` recycles connections every 30 minutes. If you still see drops, switch to a persistent PostgreSQL instance or reduce `pool_recycle`:
```python
pool_recycle=600   # Recycle every 10 min
```

---

### `alembic upgrade head` fails — "relation already exists"

**Cause:** Manual DB changes or partial migration applied.

**Fix:**
```bash
# Check current state
alembic current

# Force stamp to latest (if schema is already correct)
alembic stamp head

# Or drop and recreate (DEV ONLY)
psql -U postgres -c "DROP DATABASE eduscribe;"
psql -U postgres -c "CREATE DATABASE eduscribe;"
alembic upgrade head
```

---

### Video stuck in `PROCESSING` permanently

**Symptom:** Dashboard shows a video as "Processing" indefinitely with no progress.

**Cause:** Pipeline crashed silently. The APScheduler nightly cron only deletes *expired* videos, not stuck ones.

**Fix:**
```sql
-- Check for stuck videos (processing >2 hours)
SELECT id, title, created_at, status
FROM videos
WHERE status = 'PROCESSING'
  AND created_at < NOW() - INTERVAL '2 hours';

-- Mark as failed
UPDATE videos
SET status = 'FAILED'
WHERE status = 'PROCESSING'
  AND created_at < NOW() - INTERVAL '2 hours';
```

---

## Memory Issues

### OOM Killer (Exit Code 137 in Docker)

**Symptom:** Docker container exits unexpectedly with `Exit Code 137`.

**Cause:** faster-whisper + PaddleOCR loaded simultaneously requires 2–4 GB RAM peak. The Whisper model is unloaded after transcription to free RAM before OCR, but PaddleOCR itself needs ~500MB.

**Fix:** Increase Docker Desktop memory limit to **at least 6 GB** (Settings → Resources → Memory).

**Verify model unloading is active** in `whisper_service.py`:
```python
# After transcription completes:
del self.model
self.model = None
gc.collect()
```

---

## Frontend

### ESLint `react-hooks/exhaustive-deps` warnings

**Symptom:** `npm run lint` warns about missing hook dependencies.

**Fix:** Ensure polling functions inside `useEffect` are memoized with `useCallback`, or suppress the warning for polling intervals:
```javascript
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [videoId]);
```

---

### Transcript Explorer is blank / slow to render

**Symptom:** Workspace loads but Transcript Explorer shows nothing or freezes on long transcripts.

**Fix (now applied):** Virtual scrolling via `@tanstack/react-virtual` renders only ~20–30 visible rows. Verify the `VirtualTranscript` component is rendering in `ProjectWorkspace.jsx`.

If the transcript JSON is malformed or has no `segments` array, the component shows an empty state. Check the API response at `GET /notes/{video_id}`.

---

## Common Error Codes

| HTTP Status | Common Cause | Fix |
|---|---|---|
| `401 Unauthorized` | JWT expired or missing | Re-login at `/auth/google/login` |
| `403 Forbidden` | Accessing another user's video | Verify `user_id` in JWT matches resource |
| `413 Request Entity Too Large` | File >1GB | Reduce file size or increase `MAX_VIDEO_SIZE_MB` |
| `422 Unprocessable Entity` | Invalid request body | Check API schema in `/docs` |
| `500 Internal Server Error` | Pipeline exception | Check backend logs for traceback |

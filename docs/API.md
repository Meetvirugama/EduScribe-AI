# API Reference

The EduScribe AI backend is a FastAPI application. All endpoints except `/auth/google/login`, `/auth/google/callback`, and `/auth/exchange` require a valid JWT Bearer token.

**Base URL (dev):** `http://localhost:5001`  
**Auth header:** `Authorization: Bearer <jwt_token>`  
**Interactive docs:** `http://localhost:5001/docs` (Swagger UI)

---

## Authentication

### OAuth2 Flow

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/auth/google/login` | None | Redirects browser to Google consent screen |
| GET | `/auth/google/callback` | None | Receives `?code=` from Google; upserts user; issues one-time exchange code; redirects to `{FRONTEND_URL}/auth/callback?code=<one-time-code>` |
| POST | `/auth/exchange` | None | Accepts `{"code": "..."}`, returns `{"access_token": "..."}` JWT |
| GET | `/auth/me` | Bearer | Returns current user profile |

> **Frontend flow:** `AuthCallback.jsx` reads `?code=` from the URL, POSTs it to `/auth/exchange`, receives the JWT, stores it in `localStorage`, and navigates to `/dashboard`.

**`GET /auth/me` Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "Jane Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "is_admin": false,
  "created_at": "2026-01-15T10:00:00Z"
}
```

---

## Videos

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/videos/upload` | Bearer | Upload file (multipart/form-data) |
| POST | `/videos/youtube` | Bearer | Ingest YouTube URL |
| GET | `/videos/` | Bearer | All videos for authenticated user |
| GET | `/videos/{id}` | Bearer | Video detail + live status |
| GET | `/videos/{id}/details` | Bearer | Full metadata including transcript info |
| GET | `/videos/analytics` | Bearer | Count, total duration, total word count |
| GET | `/videos/storage` | Bearer | Storage used (SQL SUM aggregate) |
| PATCH | `/videos/{id}/retention` | Bearer | Update retention days (1–30) |
| DELETE | `/videos/{id}` | Bearer | Cascade delete all video artifacts + DB records |

### `POST /videos/upload`

**Request:** `multipart/form-data`
- `file`: Video or audio file (MP4, MKV, MOV, AVI, MP3, WAV, M4A — max `MAX_VIDEO_SIZE_MB`)
- `retention_days`: integer 1–30 (optional, default 7)

**Response:** `202 Accepted`
```json
{
  "id": "uuid",
  "title": "lecture.mp4",
  "status": "UPLOADING",
  "progress_percent": 0,
  "current_step": "Initializing",
  "created_at": "2026-08-10T10:00:00Z",
  "expires_at": "2026-08-17T10:00:00Z"
}
```

**Errors:** `400` (no filename / unsupported format), `413` (exceeds size limit), `429` (rate limit: 5 uploads/hour/user)

### `POST /videos/youtube`

**Request:** JSON body
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "retention_days": 14
}
```

Accepted YouTube hostnames: `www.youtube.com`, `youtube.com`, `youtu.be`, `m.youtube.com`, `music.youtube.com`.

**Response:** Same `202 Accepted` structure as upload.

**Errors:** `400` (invalid URL), `422` (validation error), `429` (rate limit: 10 YouTube/hour/user)

### `GET /videos/{id}`

Returns the video record with live progress fields:
```json
{
  "id": "uuid",
  "title": "Deep Learning Lecture",
  "status": "GENERATING_NOTES",
  "progress_percent": 80,
  "current_step": "Generating AI content...",
  "estimated_time_remaining_seconds": 30,
  "duration_seconds": 3600,
  "source_type": "YOUTUBE",
  "youtube_url": "https://...",
  "expires_at": "2026-08-17T10:00:00Z"
}
```

**Status values:** `UPLOADING`, `EXTRACTING_AUDIO`, `TRANSCRIBING`, `EXTRACTING_FRAMES`, `RUNNING_OCR`, `CHUNKING`, `DETECTING_TOPICS`, `GENERATING_NOTES`, `EXPORTING`, `COMPLETED`, `FAILED`

### `GET /videos/storage`

```json
{
  "used_bytes": 1073741824,
  "used_gb": 1.0,
  "video_count": 12
}
```

Computed via `SUM(file_size_bytes)` SQL aggregate — O(1) regardless of video count.

---

## Progress (SSE)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/videos/{id}/progress/stream` | Bearer | Server-Sent Events progress stream |

**Response:** `text/event-stream`

Each event is a JSON payload pushed every ~2 seconds:
```
data: {"video_id": "uuid", "status": "GENERATING_NOTES", "progress": 80, "step": "Generating AI content...", "error": null}
```

Stream closes automatically when `status` is `COMPLETED` or `FAILED`.

**Frontend usage (`useProgressStream.js`):**
```javascript
const es = new EventSource(`${API_BASE}/videos/${id}/progress/stream`, {
  headers: { Authorization: `Bearer ${token}` }
});
es.onmessage = (e) => setProgress(JSON.parse(e.data));
```

---

## Frames

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/frames/video/{video_id}` | Bearer | All frames with OCR text + scores |
| GET | `/frames/video/{video_id}/selected` | Bearer | Only `is_selected=true` frames |
| GET | `/frames/video/{video_id}/image/{frame_id}` | Bearer | Serve frame image (authenticated) |
| POST | `/frames/video/{video_id}/extract` | Bearer | Manually re-trigger vision pipeline |

### `GET /frames/video/{video_id}` Response

```json
[
  {
    "id": "uuid",
    "timestamp_ms": 165000,
    "scene_number": 5,
    "is_selected": true,
    "blur_score": 142.7,
    "visual_importance_score": 0.83,
    "transcript_similarity": 87.3,
    "ocr_text": "Gradient Descent: θ = θ - α∇J(θ)",
    "frame_path": "storage/frames/{video_id}/scene_0005_165000.jpg"
  }
]
```

**Frame image URL** (via authenticated endpoint, not static files):
```javascript
const imgUrl = `${API_BASE}/frames/video/${videoId}/image/${frameId}`;
// Always include Authorization header — frames are not publicly accessible
```

> **Note:** Frame images are served through the authenticated `frames.py` router, **not** as static files. Direct filesystem URLs (`/storage/...`) will return 404.

---

## Notes

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/notes/{video_id}` | Bearer | Markdown notes content as JSON |
| GET | `/notes/{video_id}/download` | Bearer | Download as `.md` file |
| GET | `/notes/{video_id}/search` | Bearer | Semantic search over notes |
| DELETE | `/notes/{video_id}` | Bearer | Delete the notes file |

### `GET /notes/{video_id}` Response

```json
{
  "video_id": "uuid",
  "content": "# Deep Learning Lecture\n\n**[00:00]** Welcome...\n\n### 📸 Visual Reference at 00:45\n..."
}
```

### `GET /notes/{video_id}/search?query=...`

```json
{
  "video_id": "uuid",
  "query": "gradient descent",
  "results": [
    {
      "chunk_text": "Gradient descent updates parameters by...",
      "timestamp": 142.3,
      "score": 0.87
    }
  ]
}
```

Query parameter: `query` (string, max 500 characters).

---

## Admin

All `/admin` endpoints require `is_admin=true` on the user record.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/admin/stats` | Bearer + Admin | System-wide statistics |
| GET | `/admin/users` | Bearer + Admin | All user accounts |

---

## Error Responses

All error responses use the FastAPI standard format:

```json
{
  "detail": "Human-readable error message"
}
```

Unhandled exceptions return:
```json
{
  "detail": "An unexpected error occurred. Please try again later.",
  "request_id": "uuid"
}
```

| Code | Meaning |
|---|---|
| 400 | Bad request (invalid input, unsupported URL) |
| 401 | Missing or invalid JWT token |
| 403 | Resource belongs to another user |
| 404 | Resource not found |
| 413 | File exceeds `MAX_VIDEO_SIZE_MB` |
| 422 | Pydantic validation error (malformed request body) |
| 429 | Rate limit exceeded |
| 500 | Server/pipeline error (check `request_id` in server logs) |
| 502 | External provider error (Google OAuth, yt-dlp) |

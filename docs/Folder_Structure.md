# Project Folder Structure

EduScribe AI is organised into distinct, decoupled directories.

## Root Directory

```text
EduScribe-AI/
├── backend/                # FastAPI + ARQ Python application
├── frontend/               # React 19 + Vite SPA
├── docs/                   # Markdown documentation
├── storage/                # Persistent local file storage (gitignored)
│   ├── uploads/            # Incoming video files (deleted after pipeline)
│   ├── temp/               # Temporary WAV audio files (deleted after transcription)
│   ├── transcripts/        # JSON + TXT transcript files
│   ├── frames/             # Extracted JPEG keyframes per {video_id}/
│   ├── outputs/            # Merged Markdown notes per {video_id}/
│   ├── embeddings/         # RAG vector indexes per {video_id}/
│   └── metrics/            # Quality evaluation metrics
├── docker-compose.yml      # Infrastructure orchestration
└── README.md               # Project overview
```

---

## Backend Structure

```text
backend/
├── api/
│   └── routers/
│       ├── auth.py          # Google OAuth2 + JWT issuance + /auth/exchange
│       ├── video.py         # Upload, YouTube, list, delete, storage, analytics
│       ├── frames.py        # Frame list + authenticated image serving
│       ├── notes.py         # Notes fetch, download, search, delete
│       ├── progress.py      # SSE real-time progress stream
│       └── admin.py         # Admin-only statistics endpoints
│
├── core/
│   ├── config.py            # pydantic-settings: all env vars with defaults
│   ├── database.py          # AsyncPG engine + AsyncSessionLocal
│   ├── dependencies.py      # get_owned_video + shared dependencies
│   └── security.py          # JWT create + validate + get_current_user
│
├── models/
│   ├── user.py              # User (google_id, email, name, is_admin)
│   ├── video.py             # Video + VideoStatus enum + SourceType
│   ├── transcript.py        # Transcript (video_id FK, language, word_count)
│   └── vision.py            # VideoFrame, FrameMetadata, OCRResult, FrameScore
│
├── schemas/
│   ├── video.py             # YoutubeRequest, VideoUpdateRetention, VideoResponse
│   └── content.py           # LectureState, LectureInput, ServiceStatus
│
├── services/
│           ├── ranking_service.py    # Per-scene top_n via itertools.groupby
│           ├── importance_scorer.py  # Composite score: blur + similarity + OCR
│           └── feature_extractor.py # Feature vector builder
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 8a92f814b3d2_initial_schema.py          # Base schema
│       └── 63c689249d08_add_db_indexes_and_file_size_bytes.py
│
├── main.py                  # App startup, CORS, StaticFiles, APScheduler nightly cron
├── requirements.txt
├── Dockerfile
└── .env                     # Environment variables (gitignored)
```

---

## Frontend Structure

```text
frontend/
├── src/
│   ├── assets/              # Static SVGs and images
│   │
│   ├── components/
│   │   ├── Sidebar.jsx      # Navigation sidebar
│   │   ├── UploadModal.jsx  # Add Content modal (file upload + YouTube URL)
│   │   └── ...              # Other reusable UI components
│   │
│   ├── context/
│   │   └── AuthContext.jsx  # Google OAuth2 JWT state, login/logout
│   │
│   ├── pages/
│   │   ├── LandingPage.jsx      # Public landing page
│   │   ├── AuthCallback.jsx     # Handles OAuth redirect, extracts JWT from hash
│   │   ├── Dashboard.jsx        # Video library, live progress, analytics
│   │   └── ProjectWorkspace.jsx # Transcript (virtual), Frames gallery, Notes
│   │
│   ├── App.jsx              # React Router route definitions
│   └── index.css            # Global theme, glassmorphism, animations
│
├── package.json             # npm dependencies
│   # Key packages:
│   # - react 19
│   # - react-router-dom 7
│   # - @tanstack/react-virtual  ← virtual transcript scrolling
│   # - lucide-react
│   # - vite 8
│
└── vite.config.js           # Dev server proxy + build config
```

---

## Storage Layout

```text
storage/                          ← Served by FastAPI StaticFiles at /storage
├── uploads/
│   └── {video_id}.mp4            ← Deleted after pipeline completion
│
├── temp/
│   └── {video_id}.wav            ← Deleted in pipeline finally block
│
├── transcripts/
│   ├── {video_id}.json           ← [{start, end, text}, ...]
│   └── {video_id}.txt            ← Full plaintext
│
├── frames/
│   └── {video_id}/
│       ├── scene_0001_12345.jpg  ← Selected keyframe (is_selected=True)
│       └── scene_0002_45678.jpg
│
└── outputs/
    └── {video_id}/
        └── notes.md              ← Smart Notes Markdown
```

**Frame URL:** `http://localhost:5001/storage/frames/{video_id}/scene_0001_12345.jpg`

All frame paths stored in the database are **web-relative** (e.g. `storage/frames/{video_id}/scene_0001.jpg`) — not absolute OS paths — so URL construction works identically on any deployment.

---

## docs/ Structure

```text
docs/
├── 1.FIRST_HALF.md                  # Engineering Architecture Guide (Part 1)
├── 2.SECOND_HALF.md                 # LLD Document (Part 2)
├── Engineering_Architecture.md      # Performance optimization reference
├── Features.md                      # Complete feature list
├── System_Architecture.md           # High-level architecture + request lifecycle
├── Processing_Pipeline.md           # End-to-end processing stages
├── Audio_Transcription.md           # faster-whisper + FFmpeg pipeline
├── Vision_Pipeline.md               # 9-stage computer vision pipeline
├── Frame_Extraction_Architecture.md # Detailed frame extraction LLD
├── AI_Pipeline.md                   # All AI models + algorithms
├── Backend.md                       # Backend architecture + API reference
├── Database.md                      # Schema + indexes + migrations
├── API.md                           # REST API endpoint reference
├── Tech_Stack_and_Libraries.md      # All libraries with reasoning
├── Configuration.md                 # Full .env reference + tuning guide
├── Deployment.md                    # Local dev + Docker setup
├── Troubleshooting.md               # Common issues and fixes
├── Folder_Structure.md              # This file
└── images/                          # Architecture diagrams
```

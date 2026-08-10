<div align="center">
  <h1>🎓 EduScribe AI</h1>
  <p><strong>AI-Powered Video-to-Educational-Notes Pipeline</strong></p>
</div>

EduScribe AI is a full-stack application that transforms video lectures and YouTube links into comprehensive educational notes. It chains together a speech-to-text engine, a 9-stage computer vision pipeline, a multi-provider LLM content generation system, and a semantic RAG search index — fully containerised and ready to run with a single command.

---

## What It Does

1. **Ingest** a video file (MP4/MKV/MOV/AVI/MP3/WAV) or a YouTube URL
2. **Transcribe** audio with faster-whisper (INT8, VAD filter) or pull native YouTube captions
3. **Extract** the most visually important keyframes (scene detection → dedup → blur filter → OCR → scoring)
4. **Generate** AI-authored study content — quiz, flashcards, mind map, concept map, formula sheet, revision plan, and a merged Markdown note combining transcript + frames + OCR text
5. **Index** everything into a per-video vector store for semantic search over notes
6. **Deliver** content through a React dashboard with real-time SSE progress streaming

---

## Quick Start (Docker)

```bash
git clone https://github.com/Meetvirugama/EduScribe-AI.git
cd EduScribe-AI
cp backend/.env.example backend/.env   # fill in DB URL + Google OAuth + LLM keys
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

- Frontend: `http://localhost:5173`
- API: `http://localhost:5001`
- Swagger: `http://localhost:5001/docs`

> **Requires:** Docker + Compose, Google OAuth2 credentials, and at least one LLM API key (Gemini, Groq, OpenRouter, Cohere, Cloudflare, or HuggingFace).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite, React Router, `@tanstack/react-virtual` |
| Backend | FastAPI (async), SQLAlchemy 2 (asyncpg), Alembic |
| Job Queue | ARQ (async Redis queue) |
| Speech-to-Text | faster-whisper (CTranslate2, INT8) |
| Vision | PySceneDetect, OpenCV, imagehash, PaddleOCR, RapidFuzz |
| LLM | litellm (Gemini, Groq, OpenRouter, Cohere, Cloudflare, HuggingFace) |
| Vector Store | Local file-based embeddings (Jina AI embedding model) |
| Database | PostgreSQL 15 |
| Queue/Cache | Redis 7 |
| Scheduler | APScheduler (nightly cleanup cron) |
| Auth | Google OAuth2 + JWT (HS256) |

---

## Documentation

| Doc | Contents |
|---|---|
| [System Architecture](docs/System_Architecture.md) | Component diagram, request lifecycle, storage layout |
| [Processing Pipeline](docs/Processing_Pipeline.md) | End-to-end pipeline stages (audio → vision → LLM → RAG) |
| [AI Pipeline](docs/AI_Pipeline.md) | Vision models in detail (Whisper, PySceneDetect, OpenCV, PaddleOCR) |
| [LLM & Content Generation](docs/LLM_Content_Generation.md) | LLM provider system, model selector, content services |
| [API Reference](docs/API.md) | All REST endpoints + SSE stream |
| [Database Schema](docs/Database.md) | Tables, columns, indexes, cascade rules |
| [Configuration](docs/Configuration.md) | All environment variables with defaults and guidance |
| [Deployment](docs/Deployment.md) | Local dev, Docker Compose, migrations, production checklist |
| [Troubleshooting](docs/Troubleshooting.md) | Common errors and fixes |

<div align="center">
  <h1>🎓 EduScribe AI</h1>
  <p><strong>An Intelligent Video Processing, Transcription, & Educational Notes Pipeline</strong></p>
</div>

EduScribe AI is a full-stack, AI-powered application designed to automate the extraction of knowledge from video lectures. It uses advanced computer vision and local AI models to transcribe audio, detect semantic scene changes, extract sharp, text-heavy keyframes, and automatically generate comprehensive educational notes.

## 🚀 Features & Key Capabilities

- **⚡ Blazing Fast Audio Transcription**: Utilizes OpenAI's Whisper model running locally on PyTorch to transcribe audio faster than real-time.
- **🎯 Intelligent Frame Reduction**: Automatically distills a 30fps video down to just the most visually critical slides using OpenCV and Perceptual Hashing, achieving a 99.8% reduction in visual noise.
- **📝 Deep Scene Understanding**: Uses **PaddleOCR** to read embedded text (code snippets, whiteboard writing, presentation slides) directly from extracted keyframes.
- **🔍 Semantic Transcript Matching**: Fuzzy-matches visual OCR text against the audio transcript to align slides with exact timestamps.
- **🧠 (Upcoming) AI Generated Simple Images**: Automatically generates minimal, educational textbook-style illustrations (flowcharts, architecture diagrams) based on semantic concepts extracted from the video.

## 🏗️ Technical Architecture

The project is built using a modern, scalable, containerized architecture.

### 1. Frontend (React + Vite)
- **Framework**: React.js 
- **Features**: Google Authentication, Video Upload UI, Real-time background polling, Interactive "Key Frames Gallery".

### 2. Backend (FastAPI + Python)
- **Core Engine**: FastAPI handles asynchronous API routes.
- **Background Workers**: Heavy AI processing is offloaded so the web server remains completely non-blocking.
- **Database**: PostgreSQL for storing video metadata, user profiles, OCR text, and transcript segments. Redis is utilized for high-performance task management.

## 🐳 Running the Project (Docker)

The entire application is fully Dockerized for a zero-configuration setup.

```bash
docker compose up --build -d
```
Access the application at `http://localhost:5173`.

## 📚 Project Documentation

For deep dives into specific system components, refer to the `docs/` directory:
- [System Architecture](docs/System_Architecture.md)
- [Processing Pipeline](docs/Processing_Pipeline.md)
- [AI Pipeline](docs/AI_Pipeline.md)
- [Backend & API](docs/Backend.md)
- [Database Schema](docs/Database.md)
- [Features & Roadmap](docs/Roadmap.md)

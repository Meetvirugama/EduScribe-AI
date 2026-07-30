# Roadmap

This document outlines the current progress and future trajectory of the EduScribe AI project.

## Phase 1: Foundation (✅ Completed)
- Project setup (React + FastAPI).
- PostgreSQL database design and Neon integration.
- Google OAuth authentication flow.
- Docker & Docker Compose containerization.

## Phase 2: Core Processing (✅ Completed)
- FFmpeg audio extraction and normalization.
- OpenAI Whisper local PyTorch integration.
- `yt-dlp` YouTube downloading implementation.
- Basic transcript storage and retrieval.

## Phase 3: Visual Intelligence (✅ Completed)
- OpenCV frame extraction and sub-sampling.
- Blur detection and pHash duplicate grouping.
- Visual importance scoring via edge density.
- PaddleOCR integration for text extraction.
- Semantic matching between OCR text and Whisper transcripts.

## Phase 4: Generative AI Notes (🚧 In Progress)
- **Semantic Chunking**: Grouping transcript text into logical paragraphs.
- **AI Generated Simple Images**: Generating minimal, educational textbook-style illustrations (flowcharts, architecture diagrams) based on semantic concepts extracted from the video.
- **Notes Generation**: Compiling the OCR text, Whisper transcript, and Generated Images into a comprehensive Markdown document.
- **PDF Export**: Allowing users to download the final notes as a beautifully formatted PDF.

## Phase 5: Future Scope (Planned)
- **Vector Search**: Integrating a vector database (e.g., Qdrant or Pinecone) to allow users to semantically search across their entire library of transcripts and OCR data.
- **Multi-language Support**: Translating Whisper outputs and generating localized educational images.
- **User Collaboration**: Allowing users to share Workspaces and collaboratively edit the generated notes.

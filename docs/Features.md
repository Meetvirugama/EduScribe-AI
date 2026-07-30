# Features

EduScribe AI provides a suite of advanced features designed to fully automate the transcription and visual analysis of video lectures.

## Implemented Features

### 🔐 Authentication & Security
- **Google OAuth**: Secure login using Google credentials.
- **JWT Sessions**: Stateless authentication mechanism ensuring secure API access.

### 🎥 Video Ingestion
- **Direct File Uploads**: Support for `.mp4`, `.mp3`, and `.wav`.
- **YouTube Integration**: Bypass YouTube bot protections using `yt-dlp` to directly download and process public videos.

### 🎙️ Audio Transcription
- **FFmpeg Downsampling**: Automatic normalization of audio streams.
- **OpenAI Whisper (Local)**: High-speed, high-accuracy transcription mapping words to timestamps natively on PyTorch.

### 👁️ Visual Intelligence
- **OpenCV Sampling**: Extracting video frames natively at 1fps.
- **Blur Detection**: Laplacian variance filters out useless transitional frames.
- **Duplicate Detection**: Perceptual hashing (pHash) groups identical slides into scenes.
- **Visual Scoring**: Canny Edge Detection crowns the most visually dense frame in a scene as the Top Pick.
- **OCR (PaddleOCR)**: Extremely accurate text extraction from presentation slides and whiteboards.

### 🖥️ Dashboard & Workspace
- **Real-time Progress Polling**: Live updates on video processing status.
- **Interactive Transcript**: Clickable transcript segments that sync with the video.
- **Key Frames Gallery**: A visual timeline of the most important extracted slides, complete with OCR metadata.
- **Dark Mode Glassmorphism UI**: A premium, modern visual design.

---

## Upcoming Feature: AI Generated Simple Images

### 🎨 What it is
Instead of just relying on OCR text and raw video frames, the system will soon generate its own educational visuals to embed directly into the final notes.

### 📐 How it works
1. **Semantic Chunking**: The Whisper transcript is divided into logical concept blocks.
2. **Concept Extraction**: The system identifies the core educational concept being discussed (e.g., "Database relationships" or "Binary tree traversal").
3. **Prompt Generation**: The system formulates a highly specific prompt aimed at creating a *textbook-style diagram*.
4. **Simple Image Generation**: The AI generates a clean, minimalist, flat-vector illustration (e.g., flowchart, network topology).
5. **Notes Integration**: These simple diagrams are embedded directly into the final exported PDF alongside the transcript and OCR text, dramatically improving reading comprehension.

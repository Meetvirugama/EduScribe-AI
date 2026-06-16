# EduScribe AI

## Final Development Roadmap (Production-Oriented Version)

---

# New Feature Added

## Smart Retention Policy

### Problem

Educational videos, transcripts, embeddings, PDFs, notes, quizzes, and chat history consume significant storage.

Keeping everything forever increases infrastructure cost and storage requirements.

---

### Solution

Allow users to choose how long their data should be stored.

### Retention Options

* 1 Day
* 3 Days
* 7 Days
* 15 Days (Maximum)

---

### User Flow

When uploading a video:

```text
Retention Period

○ 1 Day
○ 3 Days
○ 7 Days
○ 15 Days
```

The selected retention period automatically applies to:

* Uploaded Video
* Audio Files
* Transcript
* Embeddings
* Generated Notes
* PDFs
* HTML Notes
* Mind Maps
* Flashcards
* Quiz Data
* Chat Sessions

---

### Automatic Cleanup

A scheduled worker runs periodically.

```text
Cleanup Worker
      ↓
Check Expired Content
      ↓
Delete Files
      ↓
Delete Embeddings
      ↓
Delete Chat History
      ↓
Update User Storage Usage
```

---

### Dashboard Display

```text
Operating Systems Lecture
Expires In: 5 Days

DBMS Notes
Expires In: 2 Days

Chat Session
Expires In: 9 Days
```

---

## Save Document System

### Problem

Users need a reliable way to save, export, and manage their generated educational content for offline viewing, sharing, or integrating with other note-taking tools.

### Solution

Implement a robust document saving and export system that supports multiple formats and storage destinations.

### Supported Formats

* **Notes & Summaries:** PDF, HTML, Markdown
* **Flashcards:** CSV, JSON (for Anki import)
* **Mind Maps:** PNG, SVG
* **Transcripts:** TXT, VTT

### Storage & Export Destinations

* **Local Download:** Direct download to user's device
* **Cloud Storage:** Automatically save to user's EduScribe cloud storage (Cloudflare R2/S3)
* **Third-party Integrations:** Export directly to Notion or Google Drive

---

# Updated Phase 0 — Foundation & Infrastructure

## Objective

Build the core project infrastructure.

---

## Authentication

* Google Login
* User Profile
* Session Management

---

## Backend Setup

* FastAPI
* PostgreSQL
* Redis
* Docker

---

## Storage Setup

* Local Storage
* Cloudflare R2 / S3
* File Management
* Retention Management

---

## Smart Retention System

### Features

* User-selected retention period
* Automatic expiration
* Storage tracking
* Scheduled cleanup jobs

---

## Database Updates

### users

```sql
id UUID
google_id VARCHAR
email VARCHAR
name VARCHAR
profile_image TEXT

default_retention_days INT DEFAULT 7

storage_used_bytes BIGINT

created_at TIMESTAMP
```

---

### videos

```sql
id UUID

user_id UUID

title VARCHAR

source_type VARCHAR

retention_days INT

expires_at TIMESTAMP

created_at TIMESTAMP
```

---

### chat_sessions

```sql
id UUID

user_id UUID

retention_days INT

expires_at TIMESTAMP

created_at TIMESTAMP
```

---

### generation_outputs

```sql
id UUID

generation_id UUID

output_type VARCHAR

file_path TEXT

expires_at TIMESTAMP

created_at TIMESTAMP
```

---

## Cleanup Worker

Runs every hour.

Responsible for:

* Expired Videos
* Expired Transcripts
* Expired Embeddings
* Expired Notes
* Expired PDFs
* Expired Chat History

---

# Final Phase Structure

## Phase 0

Foundation + Authentication + Storage + Smart Retention

## Phase 1

Content Processing

* Video Upload
* YouTube Processing
* Whisper Transcription

## Phase 2

RAG Infrastructure

* Chunking
* Embeddings
* Vector Search

## Phase 3

Notes Generation

* Full Notes
* Summary Notes
* Topic Notes
* Timestamp Notes

## Phase 4

RAG Chatbot

* Chat With Video
* Chat With Notes
* Source Citations

## Phase 5

Learning Tools

* Mind Maps
* Flashcards
* Quiz Generator
* Adaptive Quiz

## Phase 6

Exam Intelligence

* Important Topics
* Difficulty Prediction
* Exam Analysis
* GATE Questions

## Phase 7

Advanced AI

* AI Tutor
* AI Mock Viva
* Crash Course Generator
* Knowledge Graph

---

# Recommended MVP

## Must Complete

* Google Login
* Video Upload
* YouTube Processing
* Smart Retention Policy
* Transcript Generation
* Full Notes
* Summary Notes
* Topic Notes
* Timestamp Notes
* PDF Export
* HTML Export
* RAG Chatbot
* Flashcards
* Quiz Generator
* Mind Map Generator

---

# Advanced Features

* Adaptive Quiz
* AI Tutor
* Exam Intelligence
* AI Mock Viva
* Crash Course Generator
* Knowledge Graph

---

# Future Scope

## Personalized Learning

* Weakness Detection
* Progress Tracking
* Learning Analytics

## Advanced RAG

* Multi-Document Chat
* Notes + Video + PDF Search

## AI Mentor

* Personalized Study Guidance
* Schedule Recommendations

## Academic Intelligence

* Exam Trend Forecasting
* Performance Prediction

---

# Final Vision

EduScribe AI is a complete AI-powered learning ecosystem that transforms educational content into interactive learning experiences.

Students can:

1. Upload lectures.
2. Generate structured notes.
3. Chat with content using RAG.
4. Learn through flashcards and quizzes.
5. Revise using mind maps.
6. Analyze exam patterns.
7. Practice viva sessions.
8. Learn through an AI tutor.

The platform combines:

* Speech AI
* NLP
* Retrieval-Augmented Generation (RAG)
* Educational Analytics
* Generative AI
* Smart Data Lifecycle Management

into a production-ready educational platform.

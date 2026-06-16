# EduScribe AI — Phase 1

# Content Processing Engine

---

# Objective

Build the complete content ingestion and transcription pipeline.

Phase 1 transforms raw educational content into structured transcripts that can later be used for:

* Notes Generation
* RAG Search
* Chatbot
* Flashcards
* Quiz Generation
* Mind Maps
* AI Tutor

At the end of Phase 1, users should be able to upload a video or provide a YouTube URL and receive a searchable transcript.

---

# Phase 1 Overview

```text
Video Upload / YouTube URL
            ↓
Content Validation
            ↓
Video Storage
            ↓
Audio Extraction (FFmpeg)
            ↓
Audio Processing
            ↓
Whisper Transcription
            ↓
Transcript Storage
            ↓
Transcript Viewer
```

---

# Major Components

## 1. Video Upload System

### Supported Inputs

#### Local Video Upload

Users can upload:

```text
MP4
MOV
AVI
MKV
WEBM
```

#### YouTube URL

Example:

```text
https://youtube.com/watch?v=xxxx
```

System downloads video automatically.

---

# Upload Validation

## File Size Limits

```text
Maximum File Size

2 GB
```

## Duration Limits

```text
Maximum Duration

6 Hours
```

## Validation Checks

* File exists
* Valid extension
* Valid MIME type
* File size check
* Duration check
* Storage quota check

---

# Retention Selection

Integrated with Phase 0 Retention System.

User chooses:

```text
Retention

○ 1 Day
○ 3 Days
○ 7 Days
○ 15 Days
```

Stored in:

```sql
videos.retention_days
videos.expires_at
```

---

# Video Storage

## Local Structure

```text
storage/

users/
    {user_id}/
        videos/
            {video_id}.mp4
```

Storage metadata stored in database.

---

# Database Design

## videos

```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY,

    user_id UUID REFERENCES users(id),

    title VARCHAR(500),

    source_type VARCHAR(50),

    youtube_url TEXT,

    duration_seconds INT,

    video_path TEXT,

    status VARCHAR(50),

    retention_days INT,

    expires_at TIMESTAMP,

    created_at TIMESTAMP
);
```

---

# Source Types

```text
UPLOAD
YOUTUBE
```

---

# Video Status

```text
UPLOADING
PROCESSING
TRANSCRIBING
COMPLETED
FAILED
```

---

# YouTube Processing

## Objective

Allow users to paste lecture URLs instead of downloading videos manually.

---

# Pipeline

```text
YouTube URL
      ↓
URL Validation
      ↓
yt-dlp Download
      ↓
Store Video
      ↓
Create Job
```

---

# Supported Content

* Public Videos
* Educational Lectures
* Recorded Classes

---

# Stored Metadata

```text
Title
Duration
Thumbnail
Channel Name
Video URL
```

---

# Audio Extraction

## Tool

FFmpeg

---

# Pipeline

```text
Video
  ↓
FFmpeg
  ↓
Audio Extraction
  ↓
WAV File
```

---

# Audio Format

```text
WAV

16 kHz

Mono Channel
```

Whisper performs best with this format.

---

# Storage Structure

```text
audio/

{video_id}.wav
```

---

# Database Updates

Storage object created:

```text
AUDIO
```

Expiration inherited from video.

---

# Transcription Engine

## Objective

Convert speech into text.

---

# Model

Whisper Large-v3

Future:

```text
Large-v3
Turbo
Faster-Whisper
```

---

# Pipeline

```text
Audio
  ↓
Whisper
  ↓
Transcript Segments
  ↓
Transcript JSON
  ↓
Transcript Text
```

---

# Output Structure

```json
{
  "start": 12.3,
  "end": 18.9,
  "text": "Today we will discuss operating systems."
}
```

---

# Transcript Storage

## Database

```sql
CREATE TABLE transcripts (
    id UUID PRIMARY KEY,

    video_id UUID REFERENCES videos(id),

    transcript_path TEXT,

    language VARCHAR(20),

    word_count INT,

    created_at TIMESTAMP
);
```

---

# Transcript Files

```text
transcripts/

{video_id}.json
{video_id}.txt
```

---

# Supported Languages

Phase 1:

```text
English
Hindi
Gujarati
Mixed Language
```

Whisper detects language automatically.

---

# Job Processing System

Uses Phase 0 jobs table.

---

# Job Types

```text
VIDEO_UPLOAD
YOUTUBE_DOWNLOAD
AUDIO_EXTRACTION
TRANSCRIPTION
```

---

# Progress Tracking

Example:

```text
Uploading Video
10%

Extracting Audio
40%

Transcribing
75%

Completed
100%
```

---

# Error Handling

## Upload Errors

```text
Invalid Format
File Too Large
Upload Failed
```

---

## YouTube Errors

```text
Video Unavailable
Private Video
Region Restricted
Download Failed
```

---

## Whisper Errors

```text
Audio Corrupted
Model Failure
Timeout
```

---

# Transcript Viewer

## Features

Users can:

* Read Transcript
* Search Transcript
* Copy Transcript
* Download Transcript

---

# Transcript Search

Basic keyword search.

Example:

```text
Search:

Binary Search
```

System highlights matching sections.

---

# Dashboard Updates

Each uploaded video displays:

```text
Operating Systems Lecture

Status: Completed

Duration: 2h 15m

Language: English

Transcript: Ready

Expires In: 7 Days
```

---

# Backend APIs

## Upload

```http
POST /videos/upload
```

---

## YouTube Import

```http
POST /videos/youtube
```

---

## Video Details

```http
GET /videos/{id}
```

---

## Video List

```http
GET /videos
```

---

## Transcript

```http
GET /videos/{id}/transcript
```

---

## Job Status

```http
GET /jobs/{id}
```

---

# Storage Objects Generated

For every processed video:

```text
VIDEO
AUDIO
TRANSCRIPT_JSON
TRANSCRIPT_TEXT
```

All inherit the same expiration date.

---

# Deliverables

## Upload System

* Video Upload
* Validation
* Storage

## YouTube Processing

* URL Input
* Download Pipeline
* Metadata Extraction

## Audio Pipeline

* FFmpeg Integration
* Audio Storage

## Transcription

* Whisper Integration
* Language Detection
* Transcript Generation

## Dashboard

* Progress Tracking
* Status Updates
* Transcript Viewer

## Storage

* Retention Integration
* Expiration Tracking
* Storage Accounting

---

# Exit Criteria

Phase 1 is complete when:

✓ User uploads video

✓ User imports YouTube lecture

✓ Video stored successfully

✓ Audio extracted using FFmpeg

✓ Whisper generates transcript

✓ Transcript stored in database

✓ Transcript files saved

✓ Progress tracking works

✓ Retention policy applies automatically

✓ User can view transcript

✓ User can search transcript

✓ Dashboard displays processing status

The output of Phase 1 is a fully structured transcript that becomes the input for Phase 2 (RAG Infrastructure) and Phase 3 (Notes Generation).

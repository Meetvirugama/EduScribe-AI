# EduScribe AI — Phase 0

## Foundation, Infrastructure & Smart Retention System

---

# Objective

Build the production-ready foundation of EduScribe AI before implementing any AI features.

Phase 0 focuses on:

* Authentication
* User Management
* Database Infrastructure
* Redis Infrastructure
* Storage Management
* Smart Retention System
* Cleanup Automation
* Deployment Setup

At the end of Phase 0, the platform should be fully deployable and ready for content processing in Phase 1.

---

# Goals

By the completion of Phase 0:

* User authentication works
* Sessions are managed securely
* PostgreSQL is connected
* Redis is connected
* Docker deployment works
* Storage architecture is established
* Smart retention policies work
* Automatic cleanup system works
* Storage tracking works
* Foundation is ready for future AI pipelines

---

# Technology Stack

## Frontend

* Next.js
* Tailwind CSS
* ShadCN UI

## Backend

* FastAPI
* SQLAlchemy
* Alembic

## Database

* PostgreSQL

## Cache

* Redis

## Authentication

* Google OAuth

## Storage

* Local Storage
* Cloudflare R2 Ready

## Deployment

* Docker
* Docker Compose

---

# System Architecture

```text
User
  ↓
Google Login
  ↓
FastAPI Backend
  ↓
PostgreSQL
  ↓
Redis
  ↓
Storage Manager
  ↓
Retention Engine
  ↓
Cleanup Worker
```

---

# Authentication Module

## Features

### Google Login

Users can sign in using Google.

### Session Management

System manages:

* Access Token
* Refresh Token
* Session Validation

### User Profile

Store:

* Name
* Email
* Profile Image
* Account Creation Time

---

# Database Design

## users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,

    google_id VARCHAR(255) UNIQUE,

    email VARCHAR(255) UNIQUE,

    name VARCHAR(255),

    profile_image TEXT,

    default_retention_days INT DEFAULT 7,

    storage_used_bytes BIGINT DEFAULT 0,

    created_at TIMESTAMP,

    updated_at TIMESTAMP
);
```

Purpose:

* User authentication
* Retention preferences
* Storage tracking

---

## jobs

Future processing jobs are tracked here.

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,

    user_id UUID REFERENCES users(id),

    job_type VARCHAR(100),

    status VARCHAR(50),

    progress INT DEFAULT 0,

    metadata JSONB,

    created_at TIMESTAMP,

    updated_at TIMESTAMP
);
```

Future Job Types:

* TRANSCRIPTION
* EMBEDDING
* NOTES_GENERATION
* QUIZ_GENERATION
* MINDMAP_GENERATION

---

## storage_objects

Tracks every stored file.

```sql
CREATE TABLE storage_objects (
    id UUID PRIMARY KEY,

    user_id UUID REFERENCES users(id),

    object_type VARCHAR(100),

    file_path TEXT,

    file_size BIGINT,

    expires_at TIMESTAMP,

    is_deleted BOOLEAN DEFAULT FALSE,

    deleted_at TIMESTAMP,

    created_at TIMESTAMP
);
```

Object Types:

* VIDEO
* AUDIO
* TRANSCRIPT
* EMBEDDING
* PDF
* HTML
* NOTE
* QUIZ
* FLASHCARD
* MINDMAP

---

## chat_sessions

Prepared for future chatbot functionality.

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,

    user_id UUID REFERENCES users(id),

    retention_days INT,

    expires_at TIMESTAMP,

    created_at TIMESTAMP
);
```

---

# Redis Infrastructure

## Usage

### Session Cache

```text
session:{user_id}
```

### Rate Limiting

```text
rate_limit:{ip}
```

### User Cache

```text
cache:user_profile:{user_id}
```

### Future Queue Preparation

Prepared for worker integration in future phases.

---

# Storage Architecture

## Local Storage Structure

```text
storage/

├── users/
│
├── videos/
│
├── audio/
│
├── transcripts/
│
├── embeddings/
│
├── notes/
│
├── exports/
│
├── quizzes/
│
├── flashcards/
│
├── mindmaps/
│
└── temp/
```

---

## User Storage Structure

```text
storage/

└── users/
    └── {user_id}/
        ├── videos/
        ├── transcripts/
        ├── notes/
        ├── exports/
        └── temp/
```

---

# Cloudflare R2 Preparation

Future cloud structure:

```text
eduscribe/

users/
    {user_id}/
        videos/
        transcripts/
        notes/
        exports/
```

Storage must be abstracted through:

```python
StorageProvider

LocalStorageProvider

R2StorageProvider
```

This allows switching storage providers without changing business logic.

---

# Smart Retention System

## Purpose

Reduce infrastructure costs by automatically deleting expired content.

---

## Supported Retention Options

```text
1 Day
3 Days
7 Days
15 Days
```

---

## User Default Retention

Users can configure:

```text
Default Retention

○ 1 Day
○ 3 Days
○ 7 Days
○ 15 Days
```

Stored in:

```sql
default_retention_days
```

---

## Expiration Calculation

Example:

```text
Upload Time

2026-06-07 10:00

Retention

7 Days
```

Automatically generates:

```text
Expires At

2026-06-14 10:00
```

---

## Applies To

Retention applies to:

* Videos
* Audio Files
* Transcripts
* Embeddings
* Notes
* PDFs
* HTML Notes
* Flashcards
* Quizzes
* Mind Maps
* Chat Sessions

---

# Storage Usage Tracking

Every uploaded or generated file updates:

```text
storage_used_bytes
```

Example Dashboard:

```text
Storage Usage

523 MB Used
```

Future plans:

```text
Free Tier

2 GB

Premium Tier

50 GB
```

---

# Cleanup Worker

## Schedule

Runs every hour.

```text
00:00
01:00
02:00
03:00
...
```

---

## Workflow

```text
Cleanup Worker
      ↓
Find Expired Objects
      ↓
Delete Physical Files
      ↓
Delete Metadata
      ↓
Update User Storage
      ↓
Mark Deleted
```

---

## Deletion Policy

### Step 1

Soft Delete

```sql
is_deleted = TRUE
deleted_at = CURRENT_TIMESTAMP
```

### Step 2

Permanent Delete After 24 Hours

Allows recovery from accidental deletion.

---

# API Endpoints

## Authentication

```http
GET  /auth/google/login

GET  /auth/google/callback

POST /auth/logout

GET  /auth/me
```

---

## User

```http
GET /users/me

PUT /users/me

PUT /users/retention
```

---

## Storage

```http
GET /storage/usage

GET /storage/objects
```

---

## Health Checks

```http
GET /health

GET /health/db

GET /health/redis

GET /health/storage
```

---

# Frontend Pages

```text
/
login
dashboard
profile
settings
```

---

# Dashboard

Displays:

```text
Welcome User

Storage Used

Default Retention

Recent Activity
```

---

# Settings

```text
Default Retention

○ 1 Day
○ 3 Days
○ 7 Days
○ 15 Days
```

---

# Docker Setup

Services:

```yaml
postgres
redis
backend
frontend
```

Start everything:

```bash
docker compose up
```

---

# Deliverables

## Authentication

* Google Login
* Logout
* Session Management
* User Profile

## Infrastructure

* FastAPI
* PostgreSQL
* Redis
* Docker

## Storage

* Local Storage
* Storage Tracking
* Storage APIs

## Retention

* User Retention Settings
* Expiration Calculation
* Cleanup Worker
* Storage Dashboard

## Deployment

* One-command startup
* Production-ready configuration

---

# Exit Criteria

Phase 0 is complete when:

* Google Login works
* User data is stored in PostgreSQL
* Redis is operational
* Storage directories are automatically created
* Retention settings function correctly
* Expiration timestamps are generated correctly
* Cleanup worker deletes expired content
* Storage usage is tracked accurately
* Health APIs pass
* Docker deployment succeeds

The platform is now ready for Phase 1: Content Processing Engine.

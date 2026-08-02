# Frame Extraction Architecture

## Table of Contents
1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Existing Pipeline](#3-existing-pipeline)
4. [New Pipeline](#4-new-pipeline)
5. [Architecture Diagram](#5-architecture-diagram)
6. [Folder Structure](#6-folder-structure)
7. [Component Overview](#7-component-overview)
8. [Scene Detection](#8-scene-detection)
9. [Frame Extraction](#9-frame-extraction)
10. [Blur Detection](#10-blur-detection)
11. [Duplicate Removal](#11-duplicate-removal)
12. [OCR](#12-ocr)
13. [Transcript Matching](#13-transcript-matching)
14. [Frame Scoring](#14-frame-scoring)
15. [APIs](#15-apis)
16. [Database Schema](#16-database-schema)
17. [Configuration](#17-configuration)
18. [Error Handling](#18-error-handling)
19. [Logging](#19-logging)
20. [Testing Strategy](#20-testing-strategy)
21. [Performance Optimizations](#21-performance-optimizations)
22. [Security Considerations](#22-security-considerations)
23. [Deployment Notes](#23-deployment-notes)
24. [Future Improvements](#24-future-improvements)
25. [Troubleshooting](#25-troubleshooting)
26. [References](#26-references)

---

## 1. Introduction

The **Intelligent Frame Extraction Pipeline** is a production-ready module built into EduScribe AI that enhances AI-generated educational notes by automatically selecting the most informative visual frames from lecture videos. These frames — containing slide content, diagrams, code blocks, and equations — provide visual grounding for LLM-generated notes.

All processing runs **locally** using open-source libraries. No cloud OCR or paid API is used.

---

## 2. Problem Statement

The existing EduScribe pipeline converts audio to text via Whisper. However, educational lectures contain critical visual content — slide titles, bullet points, code examples, diagrams, and mathematical equations — that is **not captured in audio alone**.

LLM-generated notes without visual context miss:
- Code blocks visible on slides but not spoken aloud
- Mathematical notation
- Structured bullet hierarchies
- Diagram labels and chart data

---

## 3. Existing Pipeline

```
Video File / YouTube URL
        │
        ▼
  FFmpeg (audio extraction)
        │
        ▼
  Whisper (transcription)
        │
        ▼
    Transcript (JSON + TXT)
        │
        ▼
  LLM Notes Generation
```

**Limitation:** Zero visual context.

---

## 4. New Pipeline

```
Video File
    │
    ▼
Scene Detection (PySceneDetect)
    │   Detects slide transitions & scene changes
    │   Adaptive downscale to 640px (6x CPU reduction)
    ▼
Frame Extraction (OpenCV) — best-of-2 adaptive
    │   Samples midpoint + 66% position per scene
    │   Keeps the sharper frame (Laplacian pre-check)
    ▼
Blur Detection (Adaptive Laplacian Variance)
    │   Adaptive threshold: max(global_min, median * 0.5)
    │   Score reused from extraction — zero extra I/O
    ▼
Duplicate Removal (dHash — NOT pHash)
    │   Stage 1: vs last unique frame O(1)
    │   Stage 2: vs deque(maxlen=50) O(N)
    ▼
OCR (PaddleOCR)
    │   Edge pre-filter skips ~40% of frames
    │   LRU cache (maxsize=500) prevents unbounded memory
    ▼
Transcript Matching (RapidFuzz)
    │   Scores visual-audio alignment via token_set_ratio
    ▼
Frame Scoring Engine
    │   Composite 0–1 importance score
    ▼
Best Frame Selection — 1 per scene (groupby fix)
    │   itertools.groupby per scene_number
    ▼
Database Persistence
    │   video_frames / frame_metadata / ocr_results / frame_scores
    │   frame_path stored as web-relative string
    ▼
LLM Notes (with visual context)
```

---

## 5. Architecture Diagram

```mermaid
graph TD
    A[Video File] --> B[SceneDetectorService\nPySceneDetect ContentDetector\n640px adaptive downscale]
    B --> C[FrameExtractorService\nOpenCV best-of-2 adaptive sampling]
    C --> D[BlurDetector\nLaplacian CV_16S + Adaptive Threshold]
    D --> E{Sharp?}
    E -- No --> DISCARD1[Discard]
    E -- Yes --> F[DuplicateDetector\ndHash + deque maxlen=50]
    F --> G{Unique?}
    G -- No --> DISCARD2[Discard]
    G -- Yes --> H[OCRService\nPaddleOCR + LRU Cache]
    H --> I[TranscriptMatcherService\nRapidFuzz token_set_ratio]
    I --> J[FrameScorer\nWeighted composite score]
    J --> K[rank_and_select_frames\nper-scene groupby]
    K --> L[(PostgreSQL\nvideo_frames / frame_scores\nweb-relative frame_path)]
    K --> M[Disk: storage/frames/video_id/]
```

### Sequence Diagram – Upload Trigger

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant BG as BackgroundTask
    participant VP as VisionPipeline
    participant DB as PostgreSQL

    U->>API: POST /videos/upload
    API->>DB: INSERT video (status=UPLOADING)
    API->>BG: add_task(process_video_pipeline_async)
    API-->>U: 200 VideoResponse

    BG->>VP: vision_pipeline.run(video_id, video_path)
    VP->>VP: detect_scenes()
    VP->>VP: extract_best_frames()
    VP->>VP: filter_blurry_frames()
    VP->>VP: deduplicate_frames()
    VP->>VP: run_ocr_batch()
    VP->>VP: match_frames_to_transcript()
    VP->>VP: rank_and_select_frames()
    VP->>DB: INSERT video_frames, frame_metadata, ocr_results, frame_scores
    BG->>DB: INSERT transcript, UPDATE video status=COMPLETED
```

---

## 6. Folder Structure

```
backend/
├── services/
│   └── vision/
│       ├── __init__.py              # Package exports
│       ├── scene_detector.py        # PySceneDetect integration
│       ├── frame_extractor.py       # OpenCV frame extraction
│       ├── blur_detector.py         # Laplacian variance filtering
│       ├── duplicate_detector.py    # pHash deduplication
│       ├── ocr_service.py           # PaddleOCR integration
│       ├── transcript_matcher.py    # RapidFuzz matching
│       ├── frame_scorer.py          # Composite scoring engine
│       └── pipeline.py              # Orchestrator
├── api/
│   └── routers/
│       └── frames.py                # REST API endpoints
├── schemas/
│   └── vision.py                    # Pydantic response models
├── models/
│   └── vision.py                    # SQLAlchemy ORM tables
├── migrations/
│   └── versions/
│       └── 4f17a290ae78_add_vision_models.py
└── tests/
    └── vision/
        ├── test_blur_detector.py
        ├── test_duplicate_detector.py
        ├── test_frame_scorer.py
        └── test_transcript_matcher.py
```

Storage layout:
```
storage/
└── frames/
    └── {video_id}/
        ├── scene_0001_5420.jpg
        ├── scene_0002_18900.jpg
        └── ...
```

---

## 7. Component Overview

| Component | File | Responsibility |
|-----------|------|----------------|
| Scene Detector | `scene_detector.py` | Splits video into semantic scenes |
| Frame Extractor | `frame_extractor.py` | Extracts sharpest mid-scene frame |
| Blur Detector | `blur_detector.py` | Filters out blurry/unusable frames |
| Duplicate Detector | `duplicate_detector.py` | Removes near-identical frames |
| OCR Service | `ocr_service.py` | Extracts slide text locally |
| Transcript Matcher | `transcript_matcher.py` | Links frames to spoken content |
| Frame Scorer | `frame_scorer.py` | Computes composite importance |
| Pipeline | `pipeline.py` | Orchestrates all steps, persists DB |
| API Router | `routers/frames.py` | REST interface |

---

## 8. Scene Detection

**Library:** PySceneDetect  
**Detector:** `ContentDetector`

### How It Works

`ContentDetector` computes a delta score between adjacent frames by comparing HSV channel histograms. When the score exceeds `SCENE_DETECT_THRESHOLD`, a scene boundary is recorded.

**Why ContentDetector?**
- Designed for real-world video (not just cuts)
- Handles fade transitions common in lecture recordings
- Fast: processes downscaled frames

**Threshold Selection:**

| Threshold | Use Case |
|-----------|----------|
| `15–20` | Very sensitive – catches minor camera moves |
| `27.0` | ✅ Recommended – balances slide transitions and noise |
| `35–50` | Lenient – misses subtle slide changes |

**Fallback:** If no scenes are detected, the entire video is treated as a single scene using OpenCV to probe the duration.

---

## 9. Frame Extraction

**Library:** OpenCV  
**Strategy:** Mid-scene sharpest frame

### Algorithm

For each scene `[start_ms, end_ms]`:
1. Seek to the **midpoint** of the scene using `cv2.CAP_PROP_POS_MSEC`
2. Read the frame and resize to **320px wide** for Laplacian scoring
3. Compute Laplacian variance (sharpness score)
4. If score is **below the adaptive blur threshold**, seek to **66%** of the scene duration and evaluate a second candidate frame
5. Keep the frame with the **higher sharpness score**
6. Write the winner to disk as JPEG quality 92
7. Return metadata including the pre-computed `blur_score`

This examines at most **2 frames per scene** instead of 5–10, reducing OpenCV decode cost by ~4x.

**Frame path format:** Web-relative strings stored in DB:
```python
web_relative_path = os.path.join("storage", "frames", video_id, filename)
# e.g. "storage/frames/abc-uuid/scene_0001_12345.jpg"
# Frontend: http://localhost:5001/{frame_path}
```

**Naming Convention:** `scene_{scene_number:04d}_{timestamp_ms}.jpg`

---

## 10. Blur Detection

**Algorithm:** Variance of Laplacian

```python
# CV_16S (16-bit signed) instead of CV_64F — 4x less matrix memory
# Better CPU cache locality → faster variance computation
gray_small = cv2.resize(frame, (320, h * 320 // w))
laplacian = cv2.Laplacian(gray_small, cv2.CV_16S)
score = float(laplacian.var())
```

**Adaptive threshold (replaces single global threshold):**
```python
import statistics
def adaptive_blur_threshold(frames):
    scores = [f["blur_score"] for f in frames if "blur_score" in f]
    if not scores:
        return BLUR_THRESHOLD   # Global fallback
    return max(BLUR_THRESHOLD, statistics.median(scores) * 0.5)
```

A single global threshold is too aggressive for low-contrast content (dark lecture slides, screen recordings). The adaptive threshold adjusts to the video's inherent sharpness range.

**Score reuse:** The `blur_score` computed during Frame Extraction is stored in the frame dict and **reused** in this stage — eliminating all disk I/O.

---

## 11. Duplicate Removal

**Library:** ImageHash (dHash — difference hash)
**Algorithm:** Pixel Gradient + Hamming Distance

> **Note:** The implementation uses `dhash`, not `phash`. dHash is 5–10x faster than pHash (no DCT computation) with equivalent accuracy for video frame deduplication.

### dHash Process

1. Resize image to 9×8 pixels
2. Convert to grayscale
3. For each row, compare adjacent pixels: left > right → 1, else → 0
4. Result: 64-bit integer hash

Two frames are duplicates if their Hamming distance `< PHASH_THRESHOLD`.

**Default Threshold:** `PHASH_THRESHOLD = 5`  
(Out of 64 bits; ~8% difference tolerance)

### Two-Stage Deduplication (O(N) optimized)

```python
from collections import deque

# Stage 1: Compare vs last unique frame only — O(1)
last_unique_hash = None

# Stage 2: Compare vs bounded deque — O(50N) = O(N)
# Replaces the previous seen_hashes: List[] which was O(N²)
seen_hashes: deque = deque(maxlen=50)
```

Recurring slides cluster in time. Checking only the last 50 unique hashes is sufficient to catch recurring title cards and repeated diagrams without the quadratic blowup.

---

## 12. OCR

**Library:** PaddleOCR (local, CPU mode)

### Configuration

```python
PaddleOCR(
    use_angle_cls=True,   # Handles rotated text
    lang="en",
    show_log=False,
    use_gpu=False,
)
```

### Text Cleaning Pipeline

1. Filter blocks with `confidence < OCR_MIN_CONFIDENCE` (default: 0.70)
2. Deduplicate lines (preserve order)
3. Remove single-character noise lines
4. Normalise Unicode (smart quotes → straight quotes)
5. Collapse multiple spaces

### Thread Safety

PaddleOCR's inference is not thread-safe. An `asyncio.Lock()` prevents concurrent calls. The service is lazy-loaded to avoid slow startup.

---

## 13. Transcript Matching

**Library:** RapidFuzz  
**Method:** `fuzz.token_set_ratio`

### Algorithm

For each frame:
1. Find the transcript segment whose time window contains `timestamp_ms`
2. If no exact match, find the segment with nearest midpoint (fallback)
3. Compute `token_set_ratio(ocr_text, segment_text)`
4. Normalise to `[0, 1]`

### Why `token_set_ratio`?

Unlike `ratio` or `partial_ratio`, `token_set_ratio` first tokenises both strings, then computes the ratio of sorted intersection vs sorted remainder. This handles:
- Word order differences (OCR reads top-to-bottom, transcript is spoken order)
- Subset relationships (slide heading matching part of a sentence)
- Case insensitivity (applied manually before calling)

**Example:**
- OCR: `"Binary Search O(log n) Array"`
- Transcript: `"Binary search runs in O of log n time on a sorted array"`
- Score: ~85

---

## 14. Frame Scoring

### Best Frame Selection — Per-Scene

```python
from itertools import groupby

# Sort by scene first, then by score descending within each scene
scored_frames.sort(key=lambda x: (x["scene_number"], -x["visual_importance_score"]))

for scene_num, scene_iter in groupby(scored_frames, key=lambda x: x["scene_number"]):
    scene_frames = list(scene_iter)
    for i, frame in enumerate(scene_frames):
        if i < top_n:    # top_n applied PER SCENE, not globally
            frame["is_selected"] = True
```

> **Critical fix:** Previous implementation applied `top_n=1` globally — selecting only 1 frame for the entire video regardless of scene count. The groupby fix selects `top_n` frames per scene, so a 30-scene lecture produces 30 selected frames.

### Weighted Formula

```
score = 0.30 × transcript_similarity
      + 0.30 × ocr_richness
      + 0.20 × educational_heuristic
      + 0.10 × sharpness
      + 0.10 × scene_duration
```

### Factor Descriptions

| Factor | Weight | Description |
|--------|--------|-------------|
| `transcript_similarity` | 30% | RapidFuzz token_set_ratio to nearest segment |
| `ocr_richness` | 30% | Normalised OCR character count (max 800 chars) |
| `educational_heuristic` | 20% | Code, equations, or bullet points detected |
| `sharpness` | 10% | Laplacian variance normalised to 1000 cap |
| `scene_duration` | 10% | Normalised against 60 s max |

### Educational Heuristic Patterns

| Pattern | Bonus |
|---------|-------|
| Code keywords (`def`, `class`, `import`, `{`, `}`) | +0.4 |
| Math symbols (`=`, `∑`, `∫`, `≤`, `√`) | +0.3 |
| Bullet markers (`•`, `-`, `*`, numbered lists) | +0.3 |

---

## 15. APIs

### `POST /videos/{video_id}/extract-frames`

**Trigger frame extraction pipeline.**

| Property | Value |
|----------|-------|
| Auth | Bearer JWT required |
| Response | `202 Accepted` |
| Body | None |

**Response:**
```json
{
  "video_id": "uuid",
  "scenes": 0,
  "frames_extracted": 0,
  "frames_selected": 0,
  "message": "Frame extraction pipeline started..."
}
```

**Errors:**
- `400` – Video not in COMPLETED state
- `400` – Video has no local file path (YouTube-only)
- `404` – Video not found

---

### `GET /videos/{video_id}/frames`

**List frames for a video.**

| Query Param | Type | Default | Description |
|-------------|------|---------|-------------|
| `selected_only` | bool | false | Return only `is_selected=True` frames |

**Frame path in response:** Web-relative string. Frontend constructs full URL:
```javascript
const url = `http://localhost:5001/${frame.frame_path}`;
// → http://localhost:5001/storage/frames/{video_id}/scene_0001_12345.jpg
```

**Response:** Array of `VideoFrameResponse`

---

### `GET /frames/{frame_id}`

**Full metadata for one frame.** Returns `VideoFrameResponse` including OCR text, blur score, pHash, transcript similarity, and visual importance score.

---

### `DELETE /videos/{video_id}/frames`

**Delete all frames** for a video (DB records + disk files).

```json
{
  "video_id": "uuid",
  "frames_deleted": 12,
  "message": "Deleted 12 frame(s) and associated metadata."
}
```

---

## 16. Database Schema

```sql
-- video_frames: one row per extracted frame
CREATE TABLE video_frames (
    id            UUID PRIMARY KEY,
    video_id      UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp_ms  INTEGER NOT NULL,
    -- IMPORTANT: stored as web-relative path (NOT absolute OS path)
    -- e.g. "storage/frames/{video_id}/scene_0001_12345.jpg"
    frame_path    VARCHAR NOT NULL,
    scene_number  INTEGER NOT NULL,
    created_at    TIMESTAMP
);

-- frame_metadata: quality metadata per frame
CREATE TABLE frame_metadata (
    id          UUID PRIMARY KEY,
    frame_id    UUID NOT NULL REFERENCES video_frames(id) ON DELETE CASCADE,
    blur_score  FLOAT,     -- Laplacian variance (CV_16S)
    phash       VARCHAR,   -- dHash hex string
    duration_ms INTEGER    -- Scene duration in ms
);

-- ocr_results: extracted text per frame
CREATE TABLE ocr_results (
    id                  UUID PRIMARY KEY,
    frame_id            UUID NOT NULL REFERENCES video_frames(id) ON DELETE CASCADE,
    raw_text            TEXT,
    clean_text          TEXT,
    average_confidence  FLOAT
);

-- frame_scores: scoring and selection results
CREATE TABLE frame_scores (
    id                      UUID PRIMARY KEY,
    frame_id                UUID NOT NULL REFERENCES video_frames(id) ON DELETE CASCADE,
    transcript_similarity   FLOAT,
    visual_importance_score FLOAT,
    is_selected             BOOLEAN DEFAULT FALSE
    -- is_selected=TRUE for the top_n frames PER SCENE (not globally)
);
```

---

## 17. Configuration

All settings are in `core/config.py` and overridable via `.env`:

```env
# Vision Pipeline
SCENE_DETECT_THRESHOLD=27.0     # PySceneDetect content delta threshold
SCENE_MIN_LEN_FRAMES=15         # Minimum scene length in frames
BLUR_THRESHOLD=100.0            # Laplacian variance cutoff
PHASH_THRESHOLD=5               # Max Hamming distance for duplicate detection
OCR_MIN_CONFIDENCE=0.70         # PaddleOCR confidence filter
TRANSCRIPT_MATCH_MIN_SCORE=10.0 # Minimum similarity to log a match

# Storage
FRAMES_DIR=../storage/frames    # Root directory for extracted frames
```

---

## 18. Error Handling

| Error | Location | Handling |
|-------|----------|---------|
| Video file not found | All services | `FileNotFoundError` → logged, pipeline aborted |
| Scene detection failure | `SceneDetectorService` | `SceneDetectionError` → caught in pipeline, re-raised as `VisionPipelineError` |
| No scenes detected | Pipeline | Logged as warning, returns empty result (not an error) |
| Frame read failure | `FrameExtractorService` | `None` returned per scene, warnings logged |
| Disk write failure | Frame extractor | Logged as error, frame skipped |
| OCR model not installed | `OCRService` | `OCRServiceError` with install instructions |
| OCR per-frame failure | Pipeline `_run_ocr_batch` | Frame gets empty OCR, pipeline continues |
| Missing transcript | `TranscriptMatcherService` | Warning logged, similarity = 0.0 |
| Invalid JSON transcript | Transcript matcher | Error logged, all frames get 0.0 similarity |
| DB connection failure | `VisionPipeline._persist` | Exception propagates to pipeline, video status set to FAILED |
| Disk full | Any file write | OSError caught, logged as critical |

### Frame Extraction is Non-Fatal

The vision pipeline is invoked inside a `try/except` in `tasks.py`. If it fails, the video transcription still completes. This prevents a vision library bug from breaking the core product.

---

## 19. Logging

All modules use Python's standard `logging` module. The root logger is configured in `main.py`:

```
2026-07-28 20:30:01 [INFO]  services.vision.pipeline: VisionPipeline.run() started for video abc-123
2026-07-28 20:30:03 [INFO]  services.vision.scene_detector: Detected 14 scenes in storage/uploads/abc-123.mp4
2026-07-28 20:30:04 [INFO]  services.vision.frame_extractor: Extracted 14 frames for video abc-123
2026-07-28 20:30:04 [INFO]  services.vision.blur_detector: Blur filter: 12 sharp, 2 blurry (adaptive_threshold=87.40)
2026-07-28 20:30:04 [INFO]  services.vision.duplicate_detector: Dedup: 10 unique, 2 duplicates removed
2026-07-28 20:30:15 [INFO]  services.vision.pipeline: Persisted 10 frames for video abc-123
2026-07-28 20:30:15 [INFO]  services.vision.pipeline: VisionPipeline complete for video abc-123: 14 scenes, 14 extracted, 14 selected
```

---

## 20. Testing Strategy

### Unit Tests

| File | Coverage |
|------|----------|
| `test_blur_detector.py` | Laplacian variance, is_blurry, batch filter, missing files |
| `test_duplicate_detector.py` | pHash computation, hamming distance, deduplication logic |
| `test_frame_scorer.py` | Score computation, heuristics, selection, edge cases |
| `test_transcript_matcher.py` | Segment matching, similarity scoring, missing transcript |

Run:
```bash
cd backend
source venv/bin/activate
python -m pytest tests/vision/ -v
```

### Integration Tests

Test the full pipeline with a real video file:
```bash
python -c "
import asyncio
from services.vision.pipeline import vision_pipeline
result = asyncio.run(vision_pipeline.run('test-uuid', '/path/to/video.mp4'))
print(result)
"
```

### Edge Cases Tested

- Uniform/blurry video (all frames blurry → graceful degradation)
- Single-scene video (no cuts detected)
- Empty OCR results (no text on slides)
- Missing transcript (zero similarity, pipeline continues)
- Duplicate slides (pHash deduplication)

---

## 21. Performance Optimizations

| Optimization | Details |
|--------------|---------|
| **Adaptive downscaled scene detection** | `downscale = frame_width // 640` reduces resolution before analysis — 6x CPU reduction |
| **Best-of-2 frame sampling** | Only 2 positions evaluated per scene (vs naive 5–10); 320px resize for blur check |
| **CV_16S Laplacian** | 16-bit signed instead of 64-bit float — 4x less matrix memory, better cache locality |
| **Score reuse** | Blur score from extraction reused in filter stage — zero extra disk I/O |
| **Adaptive blur threshold** | `max(global_min, median * 0.5)` prevents over-filtering for dark/low-contrast content |
| **dHash over pHash** | Integer gradient comparison — 5–10x faster than DCT-based pHash |
| **deque(maxlen=50) Stage 2** | Replaces O(N²) list with O(N) bounded deque for duplicate global check |
| **OCR edge pre-filter** | `has_meaningful_text()` skips ~40% of frames before running PaddleOCR |
| **LRU OCR cache** | `cachetools.LRUCache(maxsize=500)` prevents unbounded memory growth |
| **Lazy OCR load** | PaddleOCR model loaded only on first call |
| **asyncio.to_thread** | All blocking operations offloaded from the async event loop |
| **JPEG quality 92** | Balances file size and OCR readability |
| **Per-scene top_n** | `itertools.groupby` selects 1 best frame per scene (was broken: 1 globally) |
| **Idempotent persist** | Old frames deleted before re-insert — safe to re-trigger vision pipeline |

---

## 22. Security Considerations

- **No external API calls.** All processing is local.
- **Ownership verification.** Every API endpoint verifies the JWT user owns the requested video via `Video.user_id`.
- **Path traversal prevention.** Frame paths are constructed by joining `FRAMES_DIR` + `video_id` + filename; the `video_id` is always a validated UUID.
- **UUID validation.** All `video_id` and `frame_id` parameters are validated with `uuid.UUID(...)` before use; `422` is returned on malformed input.
- **Disk write limits.** Frame storage uses configurable `FRAMES_DIR` which should be on a volume-limited mount in production.

---

## 23. Deployment Notes

1. **`storage/frames/`** must be writable by the backend process.
2. PaddleOCR downloads model weights on first run (~500 MB). Pre-warm in Docker `CMD` or startup event.
3. The migration `4f17a290ae78_add_vision_models.py` must be applied: `alembic upgrade head`
4. Add `FRAMES_DIR` to `.env` to override the default path.
5. The existing `docker-compose.yml` mounts the `storage/` directory – frames are automatically persisted.

---

## 24. Future Improvements

| Feature | Description | Effort |
|---------|-------------|--------|
| **GPU OCR** | `use_gpu=True` in PaddleOCR for 5–10× speedup | Low |
| **SentenceTransformers** | Replace RapidFuzz with semantic embeddings for better matching | Medium |
| **Slide classifier** | CNN to classify slide vs. face-cam vs. whiteboard | High |
| **Whiteboard detector** | Detect hand-drawn diagrams | High |
| **Formula detector** | MathPix-style local LaTeX extraction | High |
| **Celery workers** | Offload vision pipeline from FastAPI process | Medium |
| **Per-chunk selection** | Select top frame per transcript chunk (not per video) | Low |
| **Vision-language model** | LLaVA for rich image captioning | High |

---

## 25. Troubleshooting

**Problem:** `PaddleOCR is not installed` error  
**Fix:** `pip install paddlepaddle paddleocr`

**Problem:** Scene detection finds 0 scenes  
**Fix:** Lower `SCENE_DETECT_THRESHOLD` (try 15.0) or check video codec compatibility

**Problem:** All frames are blurry  
**Fix:** Lower `BLUR_THRESHOLD` (try 50.0) – common with webcam footage

**Problem:** Duplicate frames not removed  
**Fix:** Increase `PHASH_THRESHOLD` (try 8–10) for compression-heavy streams

**Problem:** OCR extracts no text  
**Fix:** Verify PaddleOCR model weights downloaded; check `storage/frames/` for saved JPEGs

**Problem:** Migration fails  
**Fix:** Ensure `DATABASE_URL` is correctly set in `.env`; run `alembic upgrade head`

---

## 26. References

- [PySceneDetect Documentation](https://scenedetect.com/en/stable/)
- [OpenCV Laplacian](https://docs.opencv.org/4.x/d5/db5/tutorial_laplace_operator.html)
- [ImageHash pHash](https://github.com/JohannesBuchner/imagehash)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/)
- [EduScribe Phase 1 Spec](./phase_1.md)

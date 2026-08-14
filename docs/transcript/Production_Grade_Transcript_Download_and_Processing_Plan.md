# Production-Grade Transcript Download & Processing Plan

## 1. Purpose

This document defines the final production architecture and processing plan for a cross-platform transcript-download and processing system.

The system is designed to support:

- Web browsers
- Android
- iOS/iPadOS
- macOS
- Single jobs
- Batch jobs
- Caption-based transcript acquisition
- Authorized STT fallback for content the application is permitted to process
- TXT, SRT, VTT, and JSON exports
- Persistent background processing
- Retries and recovery
- Quality validation
- Cancellation
- Multi-device synchronization
- Secure storage and downloads
- Pipeline versioning
- Production observability

The system must not bypass access controls, authentication, CAPTCHAs, rate limits, regional restrictions, or other platform protections.

---

# 2. Core Architecture

```text
                         CLIENTS
                            |
          +-----------------+-----------------+
          |                 |                 |
       Android          iOS/iPadOS        Web/macOS
          |                 |                 |
          +-----------------+-----------------+
                            |
                           HTTPS
                            |
                            v
                    +---------------+
                    |   API Server  |
                    |    FastAPI    |
                    +-------+-------+
                            |
          +-----------------+-----------------+
          |                 |                 |
        Auth            Rate Limit       Idempotency
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                      Job Manager
                            |
              +-------------+-------------+
              |                           |
              v                           v
          PostgreSQL                  Redis/Queue
                                          |
                         +----------------+----------------+
                         |                |                |
                      Worker 1         Worker 2         Worker N
                         |                |                |
                         +----------------+----------------+
                                          |
                                          v
                                  Pipeline Engine
                                          |
                 +------------------------+------------------------+
                 |                        |                        |
              Metadata               Caption Path              STT Path
                 |                        |                        |
                 +------------------------+------------------------+
                                          |
                                          v
                                  Raw Artifact Store
                                          |
                                          v
                                  Canonicalization
                                          |
                                          v
                                Segment Validation
                                          |
                                          v
                                Language Validation
                                          |
                                          v
                                  Quality Analysis
                                          |
                               +----------+----------+
                               |                     |
                            ACCEPT                 REVIEW
                               |                     |
                               +----------+----------+
                                          |
                                          v
                                       Export
                                          |
                                          v
                                 Artifact Manifest
                                          |
                                          v
                                  Object Storage
                                          |
                                          v
                                    PostgreSQL
                                          |
                         +----------------+----------------+
                         |                |                |
                      Android          iOS              Web/Mac
                         |                |                |
                         +----------------+----------------+
                                          |
                                     Notification
```

---

# 3. Technology Stack

| Component | Recommended Technology |
|---|---|
| Backend API | Python + FastAPI |
| Database | PostgreSQL |
| Queue | Redis + worker system |
| Web | Next.js / React |
| Android | Kotlin + Jetpack Compose |
| iOS/iPadOS | Swift + SwiftUI |
| macOS | SwiftUI |
| Object Storage | S3-compatible storage |
| Authentication | Secure session/OAuth-based authentication |
| API | REST; optional SSE for progress |
| Deployment | Docker |
| Logging | Structured JSON logs |
| Metrics | Prometheus-compatible metrics |
| Testing | Pytest + integration tests |

Initial implementation should start with:

```text
FastAPI
+
PostgreSQL
+
Redis/one worker system
+
Object Storage
+
Web Client
```

Mobile and desktop clients can be added after the backend pipeline is stable.

---

# 4. Design Principles

The following principles are mandatory.

## 4.1 One backend, multiple clients

The transcript engine must run on the backend.

Clients should only:

- submit jobs
- display status
- display errors
- retrieve artifacts
- cancel jobs
- synchronize job state

Do not implement separate transcript-processing logic in Android, iOS, macOS, and web clients.

## 4.2 Captions first, authorized STT second

If a suitable caption source is available through an authorized mechanism, use it before performing expensive STT processing.

## 4.3 Preserve raw data

Never overwrite the original acquired artifact.

The processing flow is:

```text
RAW SOURCE
    |
    v
RAW ARTIFACT
    |
    v
CANONICAL TRANSCRIPT
    |
    v
VALIDATED TRANSCRIPT
    |
    v
QUALITY-ASSESSED RESULT
    |
    v
EXPORT ARTIFACTS
```

## 4.4 Persistent jobs

A job must continue even if:

- the browser closes
- the phone goes offline
- the desktop application closes
- the network connection disappears

## 4.5 Bounded retries

Retries must be:

- stage-specific
- bounded
- exponential
- jittered
- aware of rate limits
- disabled for permanent failures

## 4.6 No access-control bypass

The system must not use:

- CAPTCHA solving
- credential theft
- unauthorized cookies
- proxy rotation to evade restrictions
- rate-limit evasion
- unauthorized content acquisition

---

# 5. Request Lifecycle

The complete request lifecycle is:

```text
REQUEST
  |
  v
AUTHENTICATION
  |
  v
REQUEST VALIDATION
  |
  v
URL NORMALIZATION
  |
  v
REQUEST IDEMPOTENCY
  |
  v
EXISTING JOB CHECK
  |
  v
QUEUE
  |
  v
SOURCE ACCESS CHECK
  |
  v
METADATA
  |
  v
CAPTION DISCOVERY
  |
  v
SOURCE SELECTION
  |
  v
ACQUISITION
  |
  v
RAW ARTIFACT VALIDATION
  |
  v
CANONICALIZATION
  |
  v
SEGMENT VALIDATION
  |
  v
LANGUAGE VALIDATION
  |
  v
QUALITY ANALYSIS
  |
  v
REPAIR / REVIEW DECISION
  |
  v
EXPORT
  |
  v
STORAGE VERIFICATION
  |
  v
ATOMIC COMPLETION
  |
  v
CLIENT SYNCHRONIZATION
```

---

# 6. API Request

Example:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "language": "en",
  "formats": ["txt", "srt", "vtt", "json"]
}
```

The server immediately returns:

```json
{
  "job_id": "job_123456",
  "status": "QUEUED"
}
```

The API must not hold a browser/mobile connection open for the entire processing operation.

---

# 7. Authentication

Every job must belong to an authenticated user.

The backend derives:

```text
user_id
```

from the authenticated session/token.

Never trust a client-provided:

```json
{
  "user_id": "..."
}
```

for ownership decisions.

Optional device information:

```text
user_id
device_id
job_id
```

can be stored for synchronization and audit purposes.

---

# 8. URL Normalization

Normalize supported URL forms into a canonical representation.

Examples:

```text
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://www.youtube.com/shorts/VIDEO_ID
https://www.youtube.com/embed/VIDEO_ID
```

Also handle URLs containing query parameters such as:

```text
&t=120
&start=120
&list=...
&utm_*
&si=...
```

Tracking parameters should normally be ignored.

If the application supports start/end ranges, those values must be explicitly parsed and validated instead of silently discarded.

Canonical representation:

```json
{
  "source": "youtube",
  "video_id": "VIDEO_ID"
}
```

Invalid cases:

```text
empty URL
malformed URL
unsupported domain
missing video ID
invalid video ID
playlist-only URL
channel URL
search URL
unsupported source
```

Reject invalid requests before queueing expensive work.

---

# 9. Request-Level Idempotency

The client should send an idempotency key for every create-job request.

Example:

```text
Idempotency-Key: abc123
```

Store:

```text
user_id
idempotency_key
request_hash
job_id
created_at
```

If the same request is submitted again, return the original job instead of creating a duplicate.

This handles:

```text
client request
    |
    v
server accepts
    |
network timeout
    |
client retries
    |
same idempotency key
    |
same job_id
```

---

# 10. Processing Fingerprint

Do not treat "same video" as automatically meaning "same processing job."

A fingerprint should include relevant processing configuration:

```text
user_id
source
video_id
requested_language
caption_preference
translation_requested
STT configuration
pipeline version
```

Example:

```text
fingerprint =
SHA256(
    user_id +
    source +
    video_id +
    requested_language +
    processing_configuration +
    pipeline_version
)
```

Different requested languages or processing configurations can therefore create different results.

---

# 11. Processing Versioning

Every processed result must record the pipeline versions used.

Example:

```json
{
  "pipeline_version": "3.0.0",
  "parser_version": "2.1.0",
  "normalizer_version": "1.4.0",
  "quality_version": "1.2.0",
  "exporter_version": "1.1.0"
}
```

This allows:

- reproducibility
- debugging
- reprocessing
- comparison between pipeline versions
- safe migration of old results

Do not silently overwrite old processing results when a new pipeline version is introduced.

---

# 12. Metadata Stage

Obtain metadata through the permitted/authorized access mechanism.

Potential states:

```text
AVAILABLE
PRIVATE
DELETED
RESTRICTED
UNAVAILABLE
LIVE
UNKNOWN
```

Metadata availability does not guarantee later acquisition success.

A video may become unavailable between:

```text
metadata lookup
```

and:

```text
caption/audio acquisition
```

Therefore every acquisition stage must independently verify access.

---

# 13. Source Access States

Track access separately from metadata:

```text
ACCESSIBLE
ACCESS_DENIED
AUTH_REQUIRED
RATE_LIMITED
TEMPORARILY_UNAVAILABLE
REGION_RESTRICTED
AGE_RESTRICTED
MEMBERS_ONLY
PREMIERE
LIVE
ENDED_LIVE
```

Important rule:

```text
Video exists
!=
Application is allowed to acquire it
```

---

# 14. Caption Discovery

Determine whether a usable caption track is available through the permitted access path.

Possible tracks:

```text
English - manual
English - automatic
Hindi - manual
Telugu - automatic
```

Caption selection must be deterministic.

Recommended priority:

```text
Requested language
        |
        +--> exact manual caption
        |
        +--> exact automatic caption
        |
        +--> explicitly requested translation
        |
        +--> authorized STT fallback
        |
        +--> NO_TRANSCRIPT_SOURCE
```

Never silently switch from the requested language to another language.

---

# 15. Caption Acquisition

Caption discovery and acquisition are separate stages.

A discovered caption may still fail during acquisition because of:

```text
empty response
malformed payload
unsupported format
invalid encoding
truncated response
HTTP/network failure
temporary service failure
access expiration
```

Pipeline:

```text
DISCOVERY
    |
    v
ACQUISITION
    |
    v
RAW ARTIFACT VALIDATION
    |
    v
PARSING
```

---

# 16. STT Fallback

Use STT only when:

1. No usable permitted caption source exists.
2. Authorized audio/content processing is available.
3. The application is allowed to process that content.

Flow:

```text
NO_USABLE_CAPTION
       |
       v
AUTHORIZED_AUDIO_AVAILABLE?
       |
   +---+---+
   |       |
  NO      YES
   |       |
   v       v
NO_SOURCE AUDIO_VALIDATION
           |
           v
          STT
           |
           v
     RAW SEGMENTS
```

Possible STT failures:

```text
MODEL_ERROR
AUDIO_DECODE_ERROR
TIMEOUT
RESOURCE_EXHAUSTED
LANGUAGE_UNSUPPORTED
EMPTY_OUTPUT
LOW_CONFIDENCE
```

---

# 17. Raw Artifact Preservation

Never modify the raw source artifact.

Store separately:

```text
raw/
    transcript.json

processed/
    canonical.json

exports/
    transcript.txt
    transcript.srt
    transcript.vtt
    transcript.json
```

If cleaning or parsing logic later changes, the original artifact can be reprocessed without reacquiring the source.

---

# 18. Canonical Transcript Model

All source types must be converted into one canonical segment model.

Example:

```json
{
  "index": 15,
  "start": 72.41,
  "end": 76.92,
  "text": "Today we are going to study neural networks.",
  "language": "en",
  "speaker": null,
  "confidence": 0.94
}
```

Recommended fields:

```text
index
start
end
text
language
speaker
confidence
source
```

The canonical representation becomes the single source for:

- quality analysis
- search
- display
- TXT
- SRT
- VTT
- JSON

---

# 19. Parsing Validation

Validate:

```text
start >= 0
end >= 0
end > start
index is unique
text is not unexpectedly empty
timestamps are finite
segments are ordered or explicitly reorderable
```

Invalid examples:

```text
start = -10
end = 0

start = 50
end = 42

start = NaN
end = Infinity
```

Do not blindly repair invalid data unless the source format defines a deterministic repair rule.

---

# 20. Empty Transcript Handling

A successful HTTP response does not mean a successful transcript.

Example:

```text
HTTP 200
+
parser succeeds
+
0 segments
```

Result:

```text
EMPTY_TRANSCRIPT
```

Then evaluate:

```text
authorized STT available?
```

If yes:

```text
STT fallback
```

Otherwise:

```text
NO_TRANSCRIPT_SOURCE
```

Never mark an empty transcript as `COMPLETE`.

---

# 21. Duplicate and Overlap Handling

Caption systems may contain incremental or overlapping cues.

Classify overlaps as:

```text
EXACT_DUPLICATE
NEAR_DUPLICATE
INCREMENTAL_CAPTION
INDEPENDENT_OVERLAP
```

Only merge when the rule is sufficiently reliable.

Do not blindly transform:

```text
Hello
Hello everyone
Hello everyone today
Hello everyone today we're learning
```

into one segment without understanding the caption format.

Always preserve the original segments.

---

# 22. Text Normalization

Use conservative normalization:

```text
HTML removal
      |
HTML entity decoding
      |
Unicode normalization
      |
whitespace normalization
      |
safe caption-overlap cleanup
      |
optional punctuation normalization
```

Do not aggressively remove speech fillers or rewrite wording.

For example:

```text
"uh uh uh"
```

must not automatically become:

```text
""
```

because it may represent actual speech.

---

# 23. Language Validation

Track:

```text
requested_language
dominant_language
segment_language_distribution
language_confidence
```

Example:

```json
{
  "requested_language": "en",
  "dominant_language": "en",
  "distribution": {
    "en": 0.91,
    "hi": 0.07,
    "gu": 0.02
  }
}
```

Mixed-language content should not automatically be classified as incorrect.

Flag a mismatch when the evidence indicates that the transcript is substantially different from the requested language.

---

# 24. Timestamp Validation and Coverage

Validate:

```text
negative timestamps
end < start
start == end
duplicate timestamps
out-of-order segments
timestamps beyond media duration
unusually long segments
unusual overlaps
```

Calculate transcript coverage where media duration is known.

Coverage anomalies should be warnings rather than automatic errors.

A large gap may represent:

```text
normal silence
pause
slide demonstration
Q&A delay
possible missing transcript
```

Therefore:

```text
large gap != automatic failure
```

---

# 25. Educational Quality Analysis

Because the system targets educational content, inspect high-risk terms such as:

```text
numbers
formulas
units
technical terms
names
dates
URLs
code
chemical formulas
mathematical expressions
```

Examples:

```text
H2O
CO2
10^-6
3.14159
Python
TensorFlow
Schrödinger
backpropagation
```

Do not automatically correct technical terminology based only on a generic language model.

Instead produce warnings:

```json
{
  "type": "possible_term_error",
  "text": "back propagation",
  "suggestion": "backpropagation"
}
```

The warning is not proof that the original transcript is wrong.

---

# 26. Quality Assessment

Do not claim that a quality score represents transcription accuracy.

Use it as an internal quality indicator.

Possible inputs:

```text
source type
language confidence
timestamp validity
duplicate ratio
empty segment ratio
coverage
STT confidence
technical-term warnings
parser warnings
```

Example:

```json
{
  "score": 0.91,
  "level": "HIGH"
}
```

Recommended levels:

```text
HIGH
MEDIUM
LOW
```

The score should be treated as a heuristic, not a scientifically measured accuracy percentage.

---

# 27. Review Decision

```text
QUALITY
   |
   +--> HIGH
   |      |
   |      +--> EXPORT
   |
   +--> MEDIUM
   |      |
   |      +--> EXPORT + WARNINGS
   |
   +--> LOW
          |
          +--> REVIEW / REPROCESS / FAIL
```

Example warnings:

```text
Automatic captions used
Possible language mismatch
Large transcript gaps
High duplicate ratio
Low STT confidence
Possible technical-term anomalies
```

---

# 28. Export Engine

Generate artifacts from the canonical transcript.

Supported outputs:

```text
TXT
SRT
VTT
JSON
```

## TXT

```text
Today we are going to study neural networks.
```

## Timestamped TXT

```text
[00:01:12] Today we are going to study neural networks.
```

## SRT

```text
1
00:01:12,410 --> 00:01:16,920
Today we are going to study neural networks.
```

## VTT

```text
WEBVTT

00:01:12.410 --> 00:01:16.920
Today we are going to study neural networks.
```

## JSON

Must include:

```text
metadata
processing versions
quality information
language information
segments
artifact metadata
```

---

# 29. Artifact Manifest

Maintain an artifact manifest before marking the job complete.

Example:

```json
{
  "txt": {
    "status": "READY",
    "size": 12040,
    "sha256": "..."
  },
  "srt": {
    "status": "READY",
    "size": 14231,
    "sha256": "..."
  },
  "vtt": {
    "status": "READY",
    "size": 14010,
    "sha256": "..."
  },
  "json": {
    "status": "READY",
    "size": 48320,
    "sha256": "..."
  }
}
```

The job can become `COMPLETE` only after required artifacts are verified.

---

# 30. Atomic Completion

Do not do:

```text
upload TXT
update DB COMPLETE
upload SRT
upload VTT
```

Instead:

```text
Generate artifacts
       |
       v
Validate artifacts
       |
       v
Upload artifacts
       |
       v
Verify storage
       |
       v
Create/verify manifest
       |
       v
Commit completion state
```

This prevents a job from being reported as complete while files are missing.

---

# 31. Storage

Use PostgreSQL for metadata:

```text
users
devices
videos
jobs
batch_jobs
caption_tracks
transcripts
transcript_versions
artifacts
errors
job_events
```

Use object storage for large artifacts:

```text
raw transcripts
canonical transcripts
TXT
SRT
VTT
JSON
temporary processing artifacts
```

Do not store large files directly inside normal relational rows.

---

# 32. Secure Downloads

Clients should request:

```text
GET /jobs/{job_id}/artifacts/{artifact_id}
```

The backend verifies:

```text
authenticated user
+
job ownership
+
artifact existence
+
artifact status
```

Then provide a short-lived signed download URL where appropriate.

Never expose storage credentials or unrestricted bucket paths to clients.

---

# 33. Job State Machine

Recommended public state machine:

```text
CREATED
   |
   v
VALIDATING
   |
   v
QUEUED
   |
   v
PROCESSING
   |
   v
QUALITY_CHECK
   |
   v
EXPORTING
   |
   v
STORING
   |
   v
COMPLETED
```

Failure states:

```text
FAILED_RETRYABLE
FAILED_PERMANENT
CANCELLED
EXPIRED
```

Internal transient states:

```text
RETRY_WAIT
CANCELLING
```

---

# 34. Retry Policy

Classify errors.

## Permanent

```text
INVALID_URL
UNSUPPORTED_SOURCE
VIDEO_NOT_FOUND
ACCESS_DENIED
AUTH_REQUIRED
REGION_RESTRICTED
NO_TRANSCRIPT_SOURCE
QUOTA_EXCEEDED
```

Do not retry indefinitely.

## Retryable

```text
NETWORK_TIMEOUT
TEMPORARY_SERVER_ERROR
STORAGE_TEMPORARY_FAILURE
WORKER_FAILURE
TRANSIENT_SERVICE_ERROR
```

Use:

```text
exponential backoff
+
random jitter
+
maximum attempts
```

## Rate limited

```text
RATE_LIMITED
```

must respect the supplied retry timing/backoff.

Never use retries to evade platform restrictions.

---

# 35. Stage-Aware Retry

Store:

```json
{
  "stage": "CAPTION_ACQUISITION",
  "attempt": 2,
  "max_attempts": 4
}
```

If caption acquisition fails, retry that stage instead of restarting the complete pipeline.

---

# 36. Circuit Breaker

If an external dependency repeatedly fails:

```text
failure
failure
failure
failure
failure
    |
    v
CIRCUIT OPEN
    |
    v
WAIT
    |
    v
TEST
    |
 +--+--+
 |     |
OK   FAIL
 |     |
 v     v
CLOSED OPEN
```

This prevents a failing dependency from consuming all worker capacity.

---

# 37. Worker Crash Recovery

Workers must use a lease/heartbeat mechanism.

Example:

```text
worker claims job
      |
      v
PROCESSING
      |
heartbeat periodically
```

If the worker disappears:

```text
heartbeat timeout
      |
      v
job becomes recoverable
      |
      v
another worker claims it
```

A job must never remain `PROCESSING` forever because a worker crashed.

---

# 38. Cancellation

Users must be able to cancel jobs.

State transitions:

```text
PENDING/QUEUED
      |
      v
CANCELLED
```

or:

```text
PROCESSING
      |
      v
CANCELLING
      |
      v
CANCELLED
```

Workers should check cancellation between expensive stages and chunks.

Cancellation must not allow a cancelled job to later overwrite its state as `COMPLETED`.

---

# 39. Long-Video Processing

For authorized STT processing:

```text
Long video
    |
    v
Audio preparation
    |
    v
Chunking
    |
    +--> Chunk 1
    +--> Chunk 2
    +--> Chunk 3
    +--> ...
    |
    v
Timestamp correction
    |
    v
Chunk transcript merge
    |
    v
Canonical transcript
```

Persist chunk status:

```json
{
  "chunk": 12,
  "status": "COMPLETE"
}
```

If chunk 13 fails, retry only chunk 13 when safe.

---

# 40. Batch Processing

Represent a batch as a parent entity:

```text
batch_123
   |
   +-- job_001
   +-- job_002
   +-- job_003
   +-- ...
```

Batch states:

```text
PENDING
RUNNING
PARTIAL_SUCCESS
COMPLETE
FAILED
CANCELLED
```

Example:

```text
100 requested
96 completed
2 failed
2 cancelled
```

Result:

```text
PARTIAL_SUCCESS
```

One failed video must not incorrectly mark every other successful job as failed.

---

# 41. Concurrency Limits

Protect the system with:

```text
per-user concurrency limit
global concurrency limit
queue priority
resource-aware workers
```

Example:

```text
User A → max 3 active jobs
User B → max 3 active jobs
Global → max 50 active jobs
```

Limits should be configurable.

---

# 42. Quotas and Resource Limits

Protect against accidental or abusive usage.

Possible limits:

```text
maximum URLs per request
maximum video duration
maximum transcript size
maximum concurrent jobs
maximum daily processing time
maximum retry count
maximum storage
maximum audio size
maximum number of segments
```

Standard errors:

```text
QUOTA_EXCEEDED
FILE_TOO_LARGE
DURATION_LIMIT_EXCEEDED
CONCURRENCY_LIMIT
```

---

# 43. Resource Safety

Explicitly handle:

```text
0-second media
extremely long media
huge transcript
millions of segments
very large caption payload
malformed compressed response
unexpected content type
unexpected encoding
worker memory exhaustion
disk full
storage quota exceeded
```

Use streaming and size limits where applicable.

Never allow unbounded external responses to be loaded into memory.

---

# 44. Filename Safety

Never use raw external titles directly as filesystem paths.

Unsafe:

```text
{video_title}.txt
```

A title may contain:

```text
../
/
\
:
"
```

Use safe internal filenames:

```text
job_123_transcript.srt
```

Store the display title separately.

---

# 45. Multi-Device Synchronization

All clients synchronize through the backend.

Example:

```text
Android
   |
   v
POST /jobs
   |
   v
job_123
   |
   v
Backend
```

Later:

```text
Mac
   |
   v
GET /jobs
   |
   v
job_123
```

Later:

```text
iPhone
   |
   v
GET /jobs/job_123
   |
   v
COMPLETED
```

The job state lives on the backend, not inside a single device.

---

# 46. Mobile Reliability

The mobile application must not be responsible for keeping processing alive.

Flow:

```text
Phone
  |
POST job
  |
receive job_id
  |
app closes
  |
backend continues
  |
app opens later
  |
GET job status
```

This is required for reliable Android/iOS behavior.

---

# 47. Browser Independence

Browsers should communicate through the same API.

```text
Chrome
Safari
Firefox
Edge
   |
   v
HTTPS API
```

The transcript-processing implementation remains server-side.

---

# 48. Notifications

Optional notification channels:

```text
Android push
iOS push
browser notification
email
```

Example:

```text
Transcript ready

Introduction to Neural Networks

TXT | SRT | VTT | JSON
```

Notifications should not be treated as the source of truth. The backend job state remains authoritative.

---

# 49. Observability

Every job/stage should carry:

```text
request_id
job_id
user_id
worker_id
pipeline_version
stage
attempt
duration_ms
error_code
result
```

Example:

```text
job=job_123
stage=CAPTION_ACQUISITION
attempt=2
duration_ms=1832
result=RATE_LIMITED
```

Track metrics such as:

```text
jobs created
jobs completed
jobs failed
jobs cancelled
stage latency
retry rate
rate-limit rate
STT usage
caption usage
queue depth
worker utilization
storage failures
quality distribution
```

---

# 50. Standard Error Taxonomy

Use stable machine-readable error codes:

```text
INVALID_URL
UNSUPPORTED_SOURCE
VIDEO_NOT_FOUND
ACCESS_DENIED
AUTH_REQUIRED
REGION_RESTRICTED
AGE_RESTRICTED
CAPTION_NOT_FOUND
CAPTION_ACQUISITION_FAILED
CAPTION_PARSE_FAILED
NO_TRANSCRIPT_SOURCE
AUDIO_INVALID
STT_FAILED
LANGUAGE_MISMATCH
EMPTY_TRANSCRIPT
QUALITY_TOO_LOW
EXPORT_FAILED
STORAGE_FAILED
RATE_LIMITED
QUOTA_EXCEEDED
DURATION_LIMIT_EXCEEDED
CONCURRENCY_LIMIT
CANCELLED
WORKER_TIMEOUT
INTERNAL_ERROR
```

Clients can then implement deterministic UI behavior.

---

# 51. Cleanup and Retention

Separate:

```text
raw source artifacts
processed transcript
exports
temporary audio
temporary chunks
logs
```

Temporary files should be deleted according to the configured retention policy after successful processing or terminal failure.

Do not retain downloaded media/audio indefinitely when only the transcript is required.

Retention must be configurable and auditable.

---

# 52. Recommended Database Model

Core tables:

```text
users
devices

videos
  id
  source
  external_video_id
  metadata
  duration

jobs
  id
  user_id
  video_id
  status
  requested_language
  configuration_hash
  pipeline_version
  created_at
  updated_at
  started_at
  completed_at

batch_jobs
  id
  user_id
  status

batch_items
  batch_id
  job_id

caption_tracks
  id
  video_id
  language
  type
  source
  status

transcripts
  id
  job_id
  version
  source_type
  language
  quality_level
  quality_score

transcript_segments
  id
  transcript_id
  index
  start
  end
  text
  language
  speaker
  confidence

artifacts
  id
  job_id
  type
  storage_key
  size
  checksum
  status

job_events
  id
  job_id
  stage
  status
  error_code
  metadata
  created_at
```

---

# 53. Recommended Project Structure

```text
transcript-platform/
|
+-- backend/
|   +-- app/
|       +-- api/
|       |   +-- auth.py
|       |   +-- jobs.py
|       |   +-- transcripts.py
|       |   +-- artifacts.py
|       |   +-- users.py
|       |
|       +-- core/
|       |   +-- config.py
|       |   +-- security.py
|       |   +-- logging.py
|       |   +-- errors.py
|       |
|       +-- pipeline/
|       |   +-- validator.py
|       |   +-- url_normalizer.py
|       |   +-- idempotency.py
|       |   +-- metadata.py
|       |   +-- captions.py
|       |   +-- source_selector.py
|       |   +-- transcription.py
|       |   +-- parser.py
|       |   +-- canonicalizer.py
|       |   +-- cleaner.py
|       |   +-- language.py
|       |   +-- quality.py
|       |   +-- exporter.py
|       |   +-- manifest.py
|       |
|       +-- workers/
|       |   +-- transcript_worker.py
|       |   +-- recovery.py
|       |   +-- scheduler.py
|       |
|       +-- models/
|       +-- database/
|       +-- storage/
|       +-- tests/
|
+-- web/
|   +-- nextjs-app/
|
+-- android/
|   +-- kotlin-app/
|
+-- ios/
|   +-- swiftui-app/
|
+-- macos/
|   +-- swiftui-app/
|
+-- docker/
|
+-- docs/
|
+-- tests/
```

---

# 54. Final End-to-End Pipeline

```text
USER
 |
 +-- Android
 +-- iOS/iPadOS
 +-- macOS
 +-- Windows
 +-- Chrome/Safari/Firefox/Edge
 |
 v
HTTPS
 |
 v
AUTHENTICATION
 |
 v
REQUEST VALIDATION
 |
 v
URL NORMALIZATION
 |
 v
REQUEST IDEMPOTENCY
 |
 v
EXISTING JOB CHECK
 |
 +--> EXISTING RESULT --> RETURN RESULT
 |
 v
QUEUE
 |
 v
SOURCE ACCESS CHECK
 |
 +--> PERMANENT FAILURE --> FAILED_PERMANENT
 |
 v
METADATA
 |
 v
CAPTION DISCOVERY
 |
 +--> USABLE CAPTION
 |        |
 |        v
 |   CAPTION ACQUISITION
 |
 +--> NO USABLE CAPTION
          |
          v
   AUTHORIZED STT AVAILABLE?
          |
      +---+---+
      |       |
     NO      YES
      |       |
      v       v
 NO_SOURCE  AUDIO VALIDATION
                  |
                  v
                 STT
                  |
                  v
             RAW SEGMENTS
                  |
                  +---------+
                            |
                            v
                     RAW ARTIFACT
                       VALIDATION
                            |
                            v
                     CANONICALIZATION
                            |
                            v
                    SEGMENT VALIDATION
                            |
                            v
                    DUPLICATE ANALYSIS
                            |
                            v
                    TIMESTAMP ANALYSIS
                            |
                            v
                    LANGUAGE ANALYSIS
                            |
                            v
                 EDUCATIONAL TERM CHECK
                            |
                            v
                     QUALITY ANALYSIS
                            |
                +-----------+-----------+
                |                       |
              HIGH/MEDIUM             LOW
                |                       |
                v                       v
             EXPORT              REVIEW/REPROCESS
                |                       |
                +-----------+-----------+
                            |
                            v
                         TXT/SRT/VTT/JSON
                            |
                            v
                     ARTIFACT VALIDATION
                            |
                            v
                      STORAGE UPLOAD
                            |
                            v
                    STORAGE VERIFICATION
                            |
                            v
                     ARTIFACT MANIFEST
                            |
                            v
                    ATOMIC DB COMMIT
                            |
                            v
                        COMPLETED
                            |
                            v
                  MULTI-DEVICE SYNC
                            |
                            v
                       NOTIFICATION
```

---

# 55. Final Edge-Case Matrix

| Area | Edge Case | Correct Behavior |
|---|---|---|
| URL | Invalid URL | Reject before queue |
| URL | Playlist-only URL | Reject or explicitly support |
| URL | Tracking parameters | Normalize/ignore |
| URL | Start/end parameters | Explicitly parse if feature exists |
| Request | Duplicate submission | Idempotency |
| Request | Same video, different language | Separate processing configuration |
| Video | Deleted/private | Permanent failure |
| Video | Region restricted | Explicit failure |
| Access | Authentication required | Auth-required state |
| Access | Access changes during processing | Revalidate at acquisition |
| Captions | No caption | Authorized STT fallback |
| Captions | Empty caption | Treat as unusable |
| Captions | Malformed caption | Parse failure/retry |
| Captions | Wrong language | Deterministic selection/error |
| Transcript | Zero segments | Never complete |
| Transcript | Huge transcript | Enforce resource limits |
| Timestamp | Negative | Invalid |
| Timestamp | End before start | Invalid |
| Timestamp | Large gap | Warning/investigation |
| Timestamp | Overlap | Classify before merging |
| Segments | Duplicate | Conservative deduplication |
| Language | Mixed language | Analyze distribution |
| Technical terms | Possible typo | Warning, not blind correction |
| STT | Empty output | Retry/fallback/fail |
| STT | Low confidence | Quality warning |
| Job | Worker crash | Lease/heartbeat recovery |
| Job | Network disconnect | Job continues |
| Job | User cancellation | CANCELLING → CANCELLED |
| Job | Duplicate retry | Idempotency |
| Job | Stuck PROCESSING | Recovery worker |
| Batch | Partial failures | PARTIAL_SUCCESS |
| Queue | Too many jobs | Concurrency limits |
| Retry | Temporary failure | Exponential backoff |
| Retry | Permanent failure | No retry |
| Retry | Rate limited | Respect backoff |
| Storage | Upload failure | Do not complete |
| Storage | DB/storage mismatch | Reconciliation |
| Security | Wrong user accesses job | Deny access |
| Security | Malicious filename | Sanitize/internal names |
| Security | Credential exposure | Never send storage secrets |
| Resources | Disk full | Infrastructure failure/recovery |
| Resources | Memory exhaustion | Limits/chunking |
| Client | App closes | Backend continues |
| Client | Device changes | Backend synchronization |
| Versioning | Pipeline changes | Version results |
| Cleanup | Temporary audio | Retention-based deletion |
| Notifications | Duplicate notification | Idempotent notification handling |

---

# 56. Final Implementation Order

Do not implement every feature simultaneously.

## Phase 1 — Core Pipeline

```text
FastAPI
PostgreSQL
Redis/queue
One worker
Object storage

URL validation
Metadata
Caption discovery
Caption acquisition
Canonical transcript
TXT/SRT/VTT/JSON export
```

## Phase 2 — Reliability

```text
Idempotency
Retries
Backoff
Job state machine
Worker heartbeat
Crash recovery
Cancellation
Artifact manifest
Atomic completion
```

## Phase 3 — Quality

```text
Timestamp validation
Language validation
Duplicate detection
Coverage analysis
Educational terminology warnings
Quality scoring
Review/reprocess flow
```

## Phase 4 — Scale

```text
Multiple workers
Concurrency limits
Quotas
Batch jobs
Long-video chunking
Circuit breakers
Metrics
Distributed tracing
```

## Phase 5 — Clients

```text
Web
Android
iOS/iPadOS
macOS
Notifications
Multi-device synchronization
```

---

# 57. Final Production Rules

These rules should be treated as non-negotiable:

1. **Never trust client-provided ownership information.**
2. **Never mark an empty transcript as complete.**
3. **Never silently change the requested language.**
4. **Never overwrite raw source artifacts.**
5. **Never blindly merge overlapping captions.**
6. **Never treat a heuristic quality score as transcription accuracy.**
7. **Never retry permanent errors indefinitely.**
8. **Never use retries to bypass access controls or rate limits.**
9. **Never mark a job complete before artifact verification.**
10. **Never allow a worker crash to leave a job permanently stuck.**
11. **Never expose object-storage credentials to clients.**
12. **Never use untrusted video titles as filesystem paths.**
13. **Never depend on a mobile/browser process staying alive.**
14. **Never let one failed batch item incorrectly fail the entire batch.**
15. **Always version the processing pipeline.**
16. **Always preserve the raw input before normalization.**
17. **Always use stage-aware retries.**
18. **Always make job state authoritative on the backend.**
19. **Always enforce resource and concurrency limits.**
20. **Always keep external-source access within the permissions and policies applicable to the content and service.**

---

# 58. Final Architecture Principle

The most important invariant is:

```text
                    RAW SOURCE
                        |
                        v
                  RAW ARTIFACT
                        |
                        v
              CANONICAL TRANSCRIPT
                        |
                        v
              VALIDATED TRANSCRIPT
                        |
                        v
             QUALITY-ASSESSED RESULT
                        |
                        v
                    ARTIFACTS
```

Each stage should be:

- observable
- restartable
- testable
- versioned
- independently recoverable
- non-destructive

This architecture provides the foundation for a reliable production transcript-processing platform rather than a simple transcript downloader.

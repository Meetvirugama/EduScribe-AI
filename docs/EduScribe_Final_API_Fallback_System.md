EduScribe AI — Final API Fallback System

1. Purpose

EduScribe uses multiple AI providers and multiple API keys to improve:

API availability

note-generation reliability

response speed

model quality

resilience against rate limits

resilience against temporary provider failures

graceful handling of invalid keys/models

quota-aware routing

Current API inventory

Provider

Keys

Gemini

4

Groq

5

Cohere

5

Cloudflare

5

Total

19

Important: 19 API keys must NOT be assumed to mean 19 independent quota pools. Providers can enforce quotas at project, organization, account, or other shared-resource levels.

2. Core Design Principle

EduScribe should NOT use a simple fixed fallback such as:

Gemini → Groq → Cohere → Cloudflare

Instead, use health-aware, capability-aware, quota-aware fallback.

The router should think:

"Which compatible provider + account/project + API key + model is currently the best healthy candidate for this exact task?"

The fallback hierarchy is:

Task
  ↓
Capability
  ↓
Provider
  ↓
Model
  ↓
API Key
  ↓
Request
  ↓
Error Classification
  ↓
Cooldown / Disable / Retry
  ↓
Next Best Candidate

3. Complete System Architecture

                              ┌──────────────────────┐
                              │    USER REQUEST      │
                              │                      │
                              │ Generate Notes       │
                              │ Repair Notes         │
                              │ Summarize            │
                              │ Translate            │
                              │ RAG Answer           │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │     TASK ROUTER      │
                              │                      │
                              │ task_type            │
                              │ priority             │
                              │ quality requirement  │
                              │ latency requirement  │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │   CAPABILITY FILTER  │
                              │                      │
                              │ text                 │
                              │ vision               │
                              │ audio                │
                              │ transcription        │
                              │ TTS                  │
                              │ embeddings           │
                              │ reranking            │
                              └──────────┬───────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │         CANDIDATE SELECTOR              │
                    │                                         │
                    │ provider + project + key + model        │
                    │ health + quota + latency + quality      │
                    └────────────────────┬────────────────────┘
                                         │
                ┌────────────────────────┼────────────────────────┐
                │                        │                        │
                ▼                        ▼                        ▼
        ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
        │    GEMINI     │        │     GROQ      │        │    COHERE     │
        │    4 KEYS     │        │    5 KEYS     │        │    5 KEYS     │
        └───────┬───────┘        └───────┬───────┘        └───────┬───────┘
                │                        │                        │
          ┌─────┼─────┐            ┌─────┼─────┐            ┌─────┼─────┐
          ▼     ▼     ▼            ▼     ▼     ▼            ▼     ▼     ▼
         K1    K2    K3/K4         K1    K2    K3-5         K1    K2    K3-5
          │     │     │             │     │     │             │     │     │
          └─────┴─────┘             └─────┴─────┘             └─────┴─────┘
                │                        │                        │
                └────────────────────────┼────────────────────────┘
                                         │
                               No healthy candidate?
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │     CLOUDFLARE       │
                              │       5 KEYS         │
                              └──────────┬───────────┘
                                         │
                                   K1 K2 K3 K4 K5
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  ALL CANDIDATES      │
                              │       FAILED?        │
                              └──────────┬───────────┘
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                       ┌─────────────┐       ┌─────────────┐
                       │ QUEUE/RETRY │       │ GRACEFUL    │
                       │ LATER       │       │ ERROR       │
                       └─────────────┘       └─────────────┘

4. Three-Level Fallback

The system has three major fallback levels.

Level 1 — Model fallback

Use another compatible model from the same provider.

Gemini Key 2
    │
    ├── gemini-3.7-flash       ❌ 503
    │
    ├── gemini-3.6-flash       ✅
    │
    └── gemma-4-31b-it         available

Do not immediately leave Gemini because one model failed.

Level 2 — Key fallback

If the selected model/key combination fails because of a key-specific problem:

Gemini
│
├── Key 1 → 429 ❌
├── Key 2 → 503 ❌
├── Key 3 → healthy
└── Key 4 → healthy

Try the best healthy key.

Level 3 — Provider fallback

Only move to another provider when the current provider has no suitable healthy candidate.

Gemini
   ↓
Groq
   ↓
Cohere
   ↓
Cloudflare

The exact provider order should depend on the task.

5. Recommended Provider Priority

Final educational note generation

Quality should be prioritized:

Gemini
  ↓
Groq
  ↓
Cohere
  ↓
Cloudflare

Fast preprocessing

Speed should be prioritized:

Groq
  ↓
Gemini
  ↓
Cohere
  ↓
Cloudflare

Translation

Use the strongest translation-capable candidate first:

Cohere
  ↓
Gemini
  ↓
Groq
  ↓
Cloudflare

RAG generation

Cohere / Gemini
      ↓
Groq
      ↓
Cloudflare

Provider priority is a policy, not a permanent rule. The health/quality router may change the actual candidate selected.

6. Your 19-Key Structure

GEMINI
├── Gemini Key 1
├── Gemini Key 2
├── Gemini Key 3
└── Gemini Key 4

GROQ
├── Groq Key 1
├── Groq Key 2
├── Groq Key 3
├── Groq Key 4
└── Groq Key 5

COHERE
├── Cohere Key 1
├── Cohere Key 2
├── Cohere Key 3
├── Cohere Key 4
└── Cohere Key 5

CLOUDFLARE
├── Cloudflare Key 1
├── Cloudflare Key 2
├── Cloudflare Key 3
├── Cloudflare Key 4
└── Cloudflare Key 5

The system should never blindly rotate:

Key 1 → Key 2 → Key 3 → Key 4

Instead it should select the healthiest candidate.

7. Candidate Selection

Every candidate should be represented as:

Provider
  ↓
Account / Project / Organization
  ↓
API Key
  ↓
Model
  ↓
Capability
  ↓
Health state
  ↓
Quota state

Example:

{
  "provider": "gemini",
  "project_id": "project_02",
  "key_id": "gemini_3",
  "model": "models/gemini-3.7-flash",
  "capability": "text_generation",
  "status": "healthy",
  "success_rate": 0.987,
  "avg_latency_ms": 1800,
  "consecutive_failures": 0,
  "cooldown_until": null
}

8. Health-Aware Routing

Each provider/model/key combination should maintain:

status
success_count
failure_count
consecutive_failures
success_rate
average_latency
last_success_at
last_failure_at
last_error_code
cooldown_until
estimated_quota_remaining

Example:

┌──────────────────────────────────────┐
│ Gemini K2 / gemini-3.7-flash         │
├──────────────────────────────────────┤
│ Status:             HEALTHY          │
│ Success rate:       98.7%            │
│ Avg latency:        1.8 sec          │
│ Consecutive fails:  0                │
│ Last error:         none             │
│ Cooldown:           none             │
└──────────────────────────────────────┘

9. Candidate Scoring

When several candidates are healthy, calculate a routing score.

Conceptually:

candidate_score =
      quality_score
    + health_score
    + speed_score
    + quota_availability_score
    + reliability_score
    - recent_failure_penalty
    - cooldown_penalty

The exact weights should be configurable by task.

For final notes:

quality_weight > speed_weight

For preprocessing:

speed_weight > quality_weight

10. Error Classification

The error classifier is one of the most important components.

                         API RESPONSE
                              │
                              ▼
                    ┌──────────────────┐
                    │ ERROR CLASSIFIER  │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
          ▼                  ▼                   ▼
       SUCCESS            TEMPORARY          PERMANENT
          │                FAILURE             FAILURE
          │                  │                   │
          ▼                  ▼                   ▼
       RETURN          RETRY/COOLDOWN        DISABLE

11. Error Handling Rules

Error

Classification

Action

200

Success

Return response

400

Request/capability error

Do not retry same request; choose compatible model

401

Invalid authentication

Disable key

403

Access/permission

Disable or cooldown key

404

Model unavailable

Disable that model for the account/project

429

Rate/quota limit

Cooldown candidate; try next healthy candidate

500

Provider error

Retry once

502

Gateway error

Retry once, then fallback

503

Temporary unavailable

Retry once, then fallback

Timeout

Temporary failure

Retry once, then fallback

Invalid JSON

Response error

Retry once, then fallback

Empty response

Generation failure

Retry/fallback

12. HTTP 400 Is Special

A 400 must not automatically mean that the API is broken.

Examples from your API testing:

Groq Whisper
→ 400

because Whisper expects audio.

Groq Orpheus
→ 400

because Orpheus is TTS.

Gemini TTS
→ 400

because the request used the wrong response modality.

Cohere Embed
→ 400

if tested through the chat endpoint.

Therefore:

400
 ↓
Check model capability
 ↓
Is request compatible?
 ├── NO → select compatible endpoint/model
 └── YES → mark request/model issue

Never blindly rotate all 19 keys for a capability mismatch.

13. HTTP 429 Handling

429 means the candidate is currently rate/quota limited.

Request
  ↓
429
  ↓
Record failure
  ↓
Set cooldown
  ↓
Select next healthy candidate

Example:

Gemini Key 1
    ↓
429
    ↓
Cooldown 60 sec
    ↓
Gemini Key 2
    ↓
200
    ↓
RETURN

Do not permanently blacklist the key because of one 429.

14. HTTP 5xx Handling

For:

500
502
503

use bounded retry.

Request
  ↓
503
  ↓
wait 1 sec
  ↓
retry
  ↓
503
  ↓
cooldown
  ↓
next candidate

Recommended maximum:

1 retry for 5xx

Do not repeatedly retry a failing provider because it increases latency and wastes quota.

15. Timeout Handling

Request
  ↓
Timeout
  ↓
retry once
  ↓
success?
 ├── YES → return
 └── NO  → cooldown candidate
             ↓
          next candidate

Use a maximum request timeout appropriate to the task.

Long-running deep-research or large-note jobs can have a separate timeout policy.

16. Authentication Failure

For:

401

the key should be considered invalid.

Key
 ↓
401
 ↓
DISABLE KEY
 ↓
Never immediately retry same key
 ↓
Select another key

For 403, determine whether it is:

key permission problem

model access problem

account/project restriction

provider policy restriction

Then disable only the affected scope when possible.

17. 404 Handling

404
 ↓
Model unavailable
 ↓
Disable MODEL for this account/project
 ↓
Do NOT disable entire provider

Example:

Gemini
├── gemini-2.5-flash → 404 ❌
├── gemini-3.7-flash → healthy
└── gemma-4-31b → healthy

Gemini itself is still healthy.

18. Cooldown System

Recommended starting policy:

Failure

Initial cooldown

429

30–60 seconds

502

30 seconds

503

30 seconds

Timeout

20–30 seconds

Repeated 429

Exponential backoff

401

Disable key

403

Disable/cooldown affected scope

404

Disable model for that scope

400

No cooldown; fix capability/request

Use exponential backoff for repeated temporary failures:

1st failure → 30 sec
2nd failure → 60 sec
3rd failure → 120 sec
4th failure → 300 sec

Set a maximum cooldown so a candidate can eventually recover.

19. State Machine

                    ┌─────────────┐
                    │   HEALTHY   │
                    └──────┬──────┘
                           │
                      request
                           │
                           ▼
                    ┌─────────────┐
                    │   REQUEST   │
                    └──────┬──────┘
                           │
             ┌─────────────┼──────────────┐
             │             │              │
            200            429           5xx
             │             │              │
             ▼             ▼              ▼
          SUCCESS       COOLDOWN        RETRY
             │             │              │
             ▼             │        ┌─────┴─────┐
           RETURN           │        │           │
                            │      SUCCESS     FAIL
                            │        │           │
                            │        ▼           ▼
                            │      RETURN     COOLDOWN
                            │                    │
                            └────────┬───────────┘
                                     │
                                     ▼
                               NEXT CANDIDATE


401 / 403
    │
    ▼
DISABLE KEY / AFFECTED SCOPE


404
    │
    ▼
DISABLE MODEL FOR SCOPE


400
    │
    ▼
CAPABILITY / REQUEST CHECK
    │
    ├── incompatible → choose compatible model
    └── valid → record request error

20. Model-Level Fallback Example

Gemini Key 2
│
├── gemini-3.7-flash
│        ↓ 503
│
├── gemini-3.6-flash
│        ↓ 429
│
├── gemma-4-31b-it
│        ↓ 200
│
└── RETURN

No provider switch is necessary.

21. Key-Level Fallback Example

Gemini / gemini-3.7-flash
│
├── Key 1 → 429 ❌
├── Key 2 → 503 ❌
├── Key 3 → 200 ✅
└── Key 4 → not needed

Result:

Gemini Key 3
     ↓
SUCCESS
     ↓
RETURN

22. Provider-Level Fallback Example

Only if Gemini has no suitable candidate:

GEMINI
4 keys
all candidates unavailable
       │
       ▼
GROQ
5 keys
       │
       ├── Key 1 ❌
       ├── Key 2 ❌
       ├── Key 3 ✅
       │
       ▼
    RETURN

Cohere and Cloudflare are not called.

23. Complete Real-World Example

User requests:

"Create comprehensive notes for Gradient Descent."

Attempt 1

Gemini
Key 1
gemini-3.7-flash

Result:

429

Action:

Cooldown candidate

Attempt 2

Gemini
Key 2
gemini-3.7-flash

Result:

503

Action:

Retry once

Retry:

503

Action:

Cooldown candidate

Attempt 3

Gemini
Key 3
gemini-3.7-flash

Result:

200

Quality check:

91 / 100

Result:

RETURN FINAL NOTE

Groq, Cohere, and Cloudflare are never called.

24. Quality Fallback

Fallback is not only for API failures.

A successful API response can still be poor quality.

                 REQUEST
                    │
                    ▼
                  GROQ
                    │
                  200
                    │
                    ▼
             QUALITY CRITIC
                    │
             ┌──────┴──────┐
             │             │
          >= threshold   < threshold
             │             │
             ▼             ▼
           RETURN       GEMINI
                           │
                           ▼
                       QUALITY
                           │
                      ┌────┴────┐
                      │         │
                   PASS       FAIL
                      │         │
                      ▼         ▼
                   RETURN    NEXT MODEL

Example:

Groq
  ↓
200
  ↓
Quality = 64
  ↓
Gemini
  ↓
Quality = 93
  ↓
FINAL

25. Do Not Compare Every Successful Response

If:

Gemini
→ 200
→ valid
→ quality >= threshold

stop.

Do not additionally call:

Groq
Cohere
Cloudflare

just to compare responses.

This wastes:

tokens

quota

latency

API calls

26. Capability-Aware Routing

Maintain separate model pools.

TEXT_GENERATION
├── Gemini text models
├── Groq text models
├── Cohere chat models
└── Cloudflare text models

VISION
├── Gemini vision
├── Groq multimodal
└── Cohere vision

TRANSCRIPTION
├── Groq Whisper
├── Cohere transcription
└── other dedicated transcription providers

TTS
├── Groq Orpheus
└── Gemini TTS

EMBEDDING
├── Cohere Embed
└── Jina Embed

RERANKING
├── Cohere Rerank
└── Jina Rerank

SAFETY
├── Groq Prompt Guard
├── Groq Safeguard
└── OpenRouter safety models

Never put all models into one generic fallback pool.

27. Current Recommended Text Models

Based on your supplied successful API tests:

Gemini

models/gemma-4-26b-a4b-it
models/gemma-4-31b-it
models/gemini-flash-lite-latest
models/gemini-3-flash-preview
models/gemini-3.1-flash-lite-preview
models/gemini-3.1-flash-lite
models/gemini-3.5-flash
models/gemini-3.5-flash-lite
models/gemini-3.6-flash
models/gemini-3.7-flash

Groq

openai/gpt-oss-20b
openai/gpt-oss-120b
llama-3.3-70b-versatile
llama-3.1-8b-instant
qwen/qwen3.6-27b
groq/compound
groq/compound-mini
allam-2-7b

Cohere

command-a-03-2025
command-r-plus-08-2024
command-r-08-2024
command-r7b-12-2024
c4ai-aya-expanse-32b

OpenRouter

OpenRouter was tested as an additional fallback in your model tests, but your current 19-key inventory described here is:

Gemini  = 4
Groq    = 5
Cohere  = 5
Cloudflare = 5

If OpenRouter is also connected in production, it should be placed as an additional emergency provider after the primary 19-key pool.

28. Recommended Backend Components

Create a dedicated LLM infrastructure layer:

src/
└── services/
    └── llm/
        ├── provider-manager
        ├── provider-adapters
        ├── model-registry
        ├── key-manager
        ├── account-manager
        ├── health-manager
        ├── quota-manager
        ├── cooldown-manager
        ├── error-classifier
        ├── model-router
        ├── fallback-manager
        ├── retry-manager
        ├── quality-router
        └── metrics-manager

Provider Manager

Knows:

Gemini
Groq
Cohere
Cloudflare

Provider Adapters

Each provider has its own API implementation.

GeminiAdapter
GroqAdapter
CohereAdapter
CloudflareAdapter

Model Registry

Stores:

model_id
provider
capabilities
context_length
max_output
status

Key Manager

Stores:

key_id
provider
project/account
status

Never log the raw API key.

Health Manager

Tracks:

success rate
latency
failures
last error
cooldown

Quota Manager

Tracks known:

RPM
TPM
RPD
daily quota
monthly quota

where the provider exposes reliable quota information.

Fallback Manager

Determines:

What should we try next?

Quality Router

Determines:

Was the successful answer good enough?

29. Suggested Candidate Data Model

{
  "provider": "groq",
  "account_id": "account_03",
  "key_id": "groq_key_03",
  "model": "openai/gpt-oss-20b",
  "capability": "text_generation",
  "status": "healthy",
  "health_score": 97,
  "quality_score": 88,
  "success_rate": 0.98,
  "avg_latency_ms": 850,
  "consecutive_failures": 0,
  "last_error_code": null,
  "cooldown_until": null,
  "last_success_at": "2026-08-14T22:00:00"
}

30. Request Lifecycle

1. Receive request
       ↓
2. Determine task type
       ↓
3. Determine required capability
       ↓
4. Load compatible models
       ↓
5. Remove disabled candidates
       ↓
6. Remove cooldown candidates
       ↓
7. Remove quota-exhausted candidates
       ↓
8. Score remaining candidates
       ↓
9. Select best candidate
       ↓
10. Execute request
       ↓
11. Validate response
       ↓
12. Record metrics
       ↓
13. If successful → return
       ↓
14. If failed → classify error
       ↓
15. Apply retry/cooldown/disable rule
       ↓
16. Select next candidate
       ↓
17. Repeat within retry budget
       ↓
18. Queue or graceful failure

31. Retry Budget

Never allow infinite fallback.

Example:

MAX_TOTAL_ATTEMPTS = 5
MAX_SAME_MODEL_RETRIES = 1
MAX_5XX_RETRIES = 1
MAX_TIMEOUT_RETRIES = 1

Example:

Attempt 1 → Gemini K1 / Model A
Attempt 2 → Gemini K2 / Model A
Attempt 3 → Gemini K3 / Model B
Attempt 4 → Groq K2 / Model A
Attempt 5 → Cohere K1 / Model A

Then stop.

If all fail:

Queue job / return graceful error

32. Prevent Fallback Storms

When many users hit the same provider simultaneously:

100 requests
    ↓
Gemini
    ↓
429
    ↓
100 requests → Groq

This can overload Groq too.

Use:

concurrency limits

provider-level circuit breakers

cooldowns

queueing

token buckets

jittered backoff

Architecture:

Requests
   │
   ▼
Global Queue
   │
   ▼
Provider Concurrency Controller
   │
   ├── Gemini semaphore
   ├── Groq semaphore
   ├── Cohere semaphore
   └── Cloudflare semaphore

33. Circuit Breaker

Each provider should have a circuit breaker.

             HEALTHY
                │
        repeated failures
                ▼
          ┌──────────┐
          │   OPEN   │
          └────┬─────┘
               │
           cooldown
               ▼
          ┌──────────┐
          │ HALF OPEN│
          └────┬─────┘
               │
          test request
          ┌────┴────┐
          ▼         ▼
       success     fail
          │         │
          ▼         ▼
       HEALTHY      OPEN

This prevents repeatedly sending requests to a provider that is currently down.

34. Observability

Log every attempt, but never log API keys.

Example:

{
  "request_id": "req_123",
  "provider": "gemini",
  "model": "gemini-3.7-flash",
  "key_id": "gemini_03",
  "attempt": 2,
  "status_code": 429,
  "latency_ms": 1240,
  "action": "cooldown",
  "next_provider": "gemini"
}

Track:

requests
successes
failures
429 count
5xx count
timeouts
average latency
p95 latency
provider success rate
model success rate
key success rate
fallback rate
quality score

35. Final Recommended Architecture

                         ┌────────────────────┐
                         │    EduScribe User  │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │    Task Router     │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Capability Filter  │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │  Model Registry    │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Health + Quota     │
                         │ Candidate Selector │
                         └─────────┬──────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
          ┌──────────┐       ┌──────────┐       ┌──────────┐
          │  Gemini  │       │   Groq   │       │  Cohere  │
          │  4 keys  │       │  5 keys  │       │  5 keys  │
          └────┬─────┘       └────┬─────┘       └────┬─────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                                  ▼
                         ┌───────────────────┐
                         │    Cloudflare     │
                         │      5 keys       │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │ Error Classifier  │
                         └─────────┬─────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
                   429            5xx           4xx
                    │              │              │
                cooldown         retry       inspect/disable
                    │              │              │
                    └──────────────┼──────────────┘
                                   │
                                   ▼
                           Next Candidate
                                   │
                                   ▼
                              Successful?
                              /         \
                            YES          NO
                             │            │
                             ▼            ▼
                          Quality      Retry Budget
                           Check       Exhausted?
                             │            │
                        ┌────┴────┐       ▼
                        │         │     Queue /
                       PASS      FAIL   Graceful Error
                        │         │
                        ▼         ▼
                      FINAL     Escalate
                                 │
                                 ▼
                              Next Model

36. Final Rules

Rule 1

Never rotate keys blindly.

Rule 2

Never switch providers because of one temporary 429.

Rule 3

Never retry a 400 blindly.

Rule 4

Never retry a 401 with the same key.

Rule 5

Never disable an entire provider because one model failed.

Rule 6

Separate model health from key health.

Rule 7

Separate capability from availability.

Rule 8

Use cooldowns for temporary failures.

Rule 9

Use circuit breakers for provider-wide failures.

Rule 10

Stop immediately after a successful response that passes quality validation.

Rule 11

Limit total fallback attempts.

Rule 12

Never assume multiple keys equal multiple independent quotas.

Rule 13

Keep separate pools for text, vision, transcription, TTS, embeddings, reranking, and safety.

Rule 14

Track latency, success rate, quota state, and failure history.

Rule 15

Use quality fallback only when the generated answer is actually below the required quality threshold.

37. Final Strategy in One Diagram

                         REQUEST
                            │
                            ▼
                    TASK + CAPABILITY
                            │
                            ▼
                  HEALTHY CANDIDATES
                            │
                            ▼
                 ┌────────────────────┐
                 │ Best Model + Key    │
                 │ + Provider          │
                 └─────────┬──────────┘
                           │
                         CALL
                           │
             ┌─────────────┴─────────────┐
             │                           │
          SUCCESS                      FAILURE
             │                           │
             ▼                           ▼
       Validate Quality            Classify Error
             │                           │
       ┌─────┴─────┐          ┌──────────┼──────────┐
       │           │          │          │          │
      PASS        FAIL       429        5xx        4xx
       │           │          │          │          │
       ▼           ▼          ▼          ▼          ▼
     FINAL      Quality     Cooldown   Retry      Inspect
                Escalate       │          │          │
                   │           └────┬─────┘          │
                   │                │                │
                   └────────────────┼────────────────┘
                                    │
                                    ▼
                              NEXT CANDIDATE
                                    │
                                    ▼
                           Model → Key → Provider
                                    │
                                    ▼
                              Retry Budget
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                       Available            Exhausted
                         │                     │
                         ▼                     ▼
                       RETRY              QUEUE / ERROR

Final architecture

19 API keys
   ↓
Capability-aware model registry
   ↓
Health + quota tracking
   ↓
Best candidate selection
   ↓
Model fallback
   ↓
Key fallback
   ↓
Provider fallback
   ↓
Error-specific cooldown
   ↓
Circuit breaker
   ↓
Quality validation
   ↓
Final response

This should be the central LLM fallback layer for EduScribe, rather than implementing separate retry/fallback logic inside every note-generation feature.
# Free AI API Providers — Developer Reference

Consolidated reference for the free tiers of **Groq, Gemini, Cohere, Jina AI, OpenRouter, Hugging Face, and Cloudflare**. Focused on limits, quotas, models, auth, and restrictions relevant to building on the free plan.

---

## Quick Comparison

Provider

Your current tested API status

Strong use in EduScribe

Groq

✅ Multiple text models + specialized models tested

Fast LLM inference + transcription

Gemini

✅ Multiple text models tested

Notes, reasoning, multimodal processing

Cohere

✅ Multiple chat models tested

Generation + RAG endpoints

Jina AI

⚪ No new model test data supplied

Embeddings, reranking, Reader/Search

OpenRouter

✅ Multiple free models tested

LLM fallback and model diversity

Hugging Face

⚪ No new model test data supplied

Model ecosystem and inference providers

Cloudflare

⚪ No new model test data supplied

Workers AI, routing, RAG infrastructure

Key rule: a model is marked available for your API only when your actual account/key test succeeds. A model-list response alone does not guarantee that a generic text request is valid.

## 1. Groq

### Models Confirmed by Your API Test

The following models were returned by your Groq /openai/v1/models call and tested with your current API setup.

Model

Test result

Capability / use

openai/gpt-oss-20b

✅

Text / reasoning

groq/compound-mini

✅

Text / agentic

openai/gpt-oss-120b

✅

Text / reasoning

allam-2-7b

✅

Text

meta-llama/llama-prompt-guard-2-22m

✅

Prompt/safety classification

llama-3.1-8b-instant

✅

Fast text generation

groq/compound

✅

Text / agentic

meta-llama/llama-prompt-guard-2-86m

✅

Prompt/safety classification

llama-3.3-70b-versatile

✅

Text generation

qwen/qwen3.6-27b

✅

Text + image input / text output

openai/gpt-oss-safeguard-20b

✅

Safety-focused text

canopylabs/orpheus-v1-english

❌ 400

TTS; generic chat test is invalid

canopylabs/orpheus-arabic-saudi

❌ 400

TTS; generic chat test is invalid

whisper-large-v3

❌ 400

Speech-to-text; requires audio

whisper-large-v3-turbo

❌ 400

Speech-to-text; requires audio

Recommended EduScribe text pool: openai/gpt-oss-20b, openai/gpt-oss-120b, llama-3.3-70b-versatile, llama-3.1-8b-instant, qwen/qwen3.6-27b, groq/compound, groq/compound-mini.

### Free-Tier Limits

Groq limits are model- and organization-specific. Your previously tested main text models showed 30 RPM, while TPM/RPD/TPD vary by model and organization. Use the live limits returned by the Groq account/console rather than hard-coding one quota for every model.

### Model Specs

Model

Context

Max Output

llama-3.1-8b-instant

131,072

131,072

llama-3.3-70b-versatile

131,072

32,768

openai/gpt-oss-120b

131,072

65,536

openai/gpt-oss-20b

131,072

65,536

groq/compound

131,072

8,192

groq/compound-mini

131,072

8,192

### Rate-Limit Handling

429 normally means request/token quota was exceeded.

Read x-ratelimit-* and retry/reset information when available.

Use exponential backoff and respect retry-after.

Limits are organization-level; multiple keys in the same organization should not be treated as independent quota pools.

### Notes

Whisper and Orpheus failures in the generic test are capability/request mismatches, not proof that the models are unavailable.

Free tier is not unlimited.

Model availability can change; refresh /openai/v1/models periodically.

## 2. Gemini (Google AI)

### Free-Tier Limits

Metered via RPM, TPM, RPD and model-specific quotas.

Limits are associated with the Google Cloud project, not simply the API-key string.

There is no single universal RPM/TPM/RPD value for every Gemini model.

Treat 429 RESOURCE_EXHAUSTED as quota/rate exhaustion, not automatically as an invalid model.

### Models Confirmed by Your API Test

Model

Test result

Interpretation

models/gemini-3.7-flash-video-understanding-eap

✅

Specialized video model

models/gemma-4-26b-a4b-it

✅

General text generation

models/gemma-4-31b-it

✅

General text generation

models/gemini-flash-lite-latest

✅

Lightweight general text

models/gemini-3-flash-preview

✅

General Flash

models/gemini-3.1-flash-lite-preview

✅

Lightweight Flash

models/gemini-3.1-flash-lite

✅

Lightweight Flash

models/gemini-3.5-flash

✅

General Flash

models/gemini-3.5-flash-lite

✅

Lightweight Flash

models/gemini-3.6-flash

✅

General Flash

models/gemini-3.7-flash

✅

General Flash

models/gemini-robotics-er-1.6-preview

✅

Robotics

models/gemini-robotics-er-2-preview

✅

Robotics

models/gemini-2.5-flash

❌ 404

Not available to the tested new-user account

models/gemini-2.5-pro

❌ 404

Not available to the tested new-user account

models/gemini-2.5-flash-preview-tts

❌ 400

TTS; wrong response modality for text test

models/gemini-2.5-pro-preview-tts

❌ 429

Quota was 0 during test

models/gemini-flash-latest

❌ 503

Temporary service/high-demand failure

models/gemini-pro-latest

❌ 429

Quota exceeded during test

models/gemini-2.5-flash-lite

❌ 404

Not available to tested account

models/gemini-2.5-flash-image

❌ 429

Image model/quota condition

models/gemini-3.1-pro-preview

❌ 429

Quota exceeded during test

models/gemini-3.1-pro-preview-customtools

❌ 429

Quota exceeded during test

models/gemini-3-pro-image-preview

❌ 429

Image model/quota condition

models/gemini-3-pro-image

❌ 429

Image model/quota condition

models/nano-banana-pro-preview

❌ 429

Image model/quota condition

models/gemini-3.1-flash-image-preview

❌ 429

Image model/quota condition

models/gemini-3.1-flash-image

❌ 429

Image model/quota condition

models/gemini-3.1-flash-lite-image

❌ 429

Image model/quota condition

models/gemini-omni-flash-preview

❌ 429

Quota exceeded during test

models/lyria-3-clip-preview

❌ 429

Audio/music model

models/lyria-3-pro-preview

❌ 429

Audio/music model

models/gemini-3.1-flash-tts-preview

❌ 400

TTS; wrong response modality

models/gemini-2.5-computer-use-preview-10-2025

❌ 429

Specialized model/quota condition

models/antigravity-preview-05-2026

❌ 400

Specialized/preview request mismatch

models/deep-research-max-preview-04-2026

❌ 400

Specialized Deep Research flow

models/deep-research-preview-04-2026

❌ 400

Specialized Deep Research flow

models/deep-research-pro-preview-12-2025

❌ 400

Specialized Deep Research flow

Recommended EduScribe Gemini text pool: models/gemma-4-26b-a4b-it, models/gemma-4-31b-it, models/gemini-flash-lite-latest, models/gemini-3-flash-preview, models/gemini-3.1-flash-lite-preview, models/gemini-3.1-flash-lite, models/gemini-3.5-flash, models/gemini-3.5-flash-lite, models/gemini-3.6-flash, models/gemini-3.7-flash.

### Google Search Grounding

Keep grounding availability separate from ordinary generation availability.

A model successfully generating text does not imply that Search/Maps grounding is available on the same free-tier project.

### Data Privacy

Free-tier data-handling terms should be reviewed before sending sensitive educational/user content.

### Rate-Limit Handling

429 RESOURCE_EXHAUSTED → apply cooldown/backoff.

Do not permanently blacklist a model because of a temporary 429.

404 for a model → mark unavailable for that account/project.

400 → inspect capability/request modality before blacklisting.

503 → temporary provider/model failure; retry later.

## 3. Cohere

### Free-Tier Limits (Trial API Key)

Resource

Free Limit

Monthly API calls

1,000 calls/month

Chat

20 requests/min

Audio Transcription

5 requests/min

Embed

2,000 inputs/min

Image Embed

5 inputs/min

Embed Jobs

5 requests/min

Rerank

10 requests/min

Tokenize

100 requests/min

Other endpoints

500 requests/min

### Models Confirmed by Your API Test

Model

Test result

Capability

c4ai-aya-expanse-32b

✅

General multilingual text

c4ai-aya-vision-32b

✅

Vision

command-a-03-2025

✅

General chat

command-a-translate-08-2025

✅

Translation

command-a-vision-07-2025

✅

Vision

command-r-08-2024

✅

General chat

command-r-plus-08-2024

✅

General chat

command-r7b-12-2024

✅

General chat

command-a-plus-05-2026

❌ 400

Test request not accepted

command-a-reasoning-08-2025

❌ 400

Test request not accepted

command-r7b-arabic-02-2025

❌ timeout

Test timed out

cohere-transcribe-03-2026

❌ 400

Requires transcription/audio request

embed-* models

❌ 400

Require /embed, not chat

Recommended EduScribe Cohere text pool: command-a-03-2025, command-r-plus-08-2024, command-r-08-2024, command-r7b-12-2024, c4ai-aya-expanse-32b.

### Embed & Rerank

Do not test embedding models with a chat payload.

Use the Cohere Embed endpoint for embed-*.

Use the Rerank endpoint for reranking models.

A 400 from an embedding model in a chat test is a request-type mismatch, not necessarily model failure.

### Rate-Limit Handling

429 → backoff and retry after the cooldown.

Trial keys have a monthly call cap as well as endpoint-specific limits.

Track calls separately for chat, embed, rerank, and transcription.

## 4. Jina AI

### Free-Tier Limits (new API key)
> **New keys receive 10,000,000 free tokens** (one-time trial balance, shared across Search Foundation products — Embed, Rerank, Search, Reader/DeepSearch draw from the same pool).

| Service | Free Limit |
|---|---:|
| Reader API (with key) | 500 RPM |
| Reader API (no key) | 20 RPM |
| Search API | 100 RPM |
| Embeddings | 100 RPM + 100,000 TPM |
| Reranker | 100 RPM + 100,000 TPM |
| Classifier | 25 RPM + 25,000 TPM |
| Segmenter (with key) | 200 RPM |
| Segmenter (no key) | 20 RPM |
| DeepSearch | 50 RPM |
| Embedding/Reranker concurrency | 2 concurrent requests |

- **Segmenter token usage is not charged** against the free balance.
- Search requests carry a **fixed minimum charge of 10,000 tokens** each (~1,000 searches possible from the full 10M balance if nothing else is used).
- Token math example: at 500 tokens/chunk, 10M tokens ≈ 20,000 chunks embedded; at 1,000 tokens/chunk ≈ 10,000 chunks.

### Endpoints
- Embeddings: `https://api.jina.ai/v1/embeddings` — models: `jina-embeddings-v4` (32,768 tokens max input, multimodal: text/image/PDF), `jina-embeddings-v3` (8,192), `jina-embeddings-v2-*` (8,192), `jina-clip-v1/v2` (8,192), `jina-colbert-v1/v2` (8,192), Jina code embeddings (32,768).
- Reranker: `https://api.jina.ai/v1/rerank` — models: `jina-reranker-v3` (flagship, multilingual, 131K context), `jina-reranker-m0`, `jina-reranker-v2-base-multilingual`, `jina-colbert-v2`.
- Reader (URL → clean text/Markdown): `https://r.jina.ai`.
- Search (web search): `https://s.jina.ai`.
- DeepSearch (search + reason + iterate): `https://deepsearch.jina.ai/v1/chat/completions` — billed on total tokens used across the whole process.

### Licensing
⚠️ Some Jina models are released under **CC-BY-NC 4.0** (e.g., current reranker models) — non-commercial license; verify per-model license before commercial deployment.

---

## 5. OpenRouter

### Free-Tier Limits

Item

Free Tier

Platform fee

$0

Requests/minute

20 RPM

Requests/day without credits

50 RPD

Requests/day with qualifying credit purchase

1,000 RPD

Free model catalog

Dynamic

### Free Models Confirmed by Your API Test

Model

Test result

Interpretation

liquid/lfm-2.5-2.6b:free

✅

Working

nvidia/nemotron-3.5-lightning:free

✅

Working

cohere/north-mini-code:free

✅

Coding-focused

nvidia/nemotron-3.5-content-safety:free

✅

Safety-focused

nvidia/nemotron-3-ultra-550b-a55b:free

✅

Working

nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free

✅

Multimodal/reasoning

nvidia/nemotron-3-super-120b-a12b:free

✅

Working

openrouter/free

✅

Dynamic free routing

nvidia/nemotron-3-nano-30b-a3b:free

✅

Working

nvidia/nemotron-nano-12b-v2-vl:free

✅

Vision-language

nvidia/nemotron-nano-9b-v2:free

✅

Working

poolside/laguna-s-2.1:free

❌ timeout

Temporary timeout

poolside/laguna-xs-2.1:free

❌ 429

Rate limited during test

google/gemma-4-26b-a4b-it:free

❌ 429

Rate limited during test

google/gemma-4-31b-it:free

❌ 429

Rate limited during test

google/lyria-3-pro-preview

❌ 502

Upstream gateway failure

google/lyria-3-clip-preview

❌ 502

Upstream gateway failure

openai/gpt-oss-20b:free

❌ 429

Rate limited during test

Recommended EduScribe OpenRouter free pool: nvidia/nemotron-3-super-120b-a12b:free, nvidia/nemotron-3-ultra-550b-a55b:free, nvidia/nemotron-3.5-lightning:free, liquid/lfm-2.5-2.6b:free, openrouter/free, nvidia/nemotron-3-nano-30b-a3b:free, and nvidia/nemotron-nano-9b-v2:free.

### Routing

openrouter/free dynamically selects an available free model.

model-name:free pins a specific free model.

Free-model availability is dynamic; refresh the catalog and health-check before relying on a model.

429 means rate limiting/upstream quota and should normally trigger a cooldown rather than permanent removal.

### API

OpenAI-compatible base URL: https://openrouter.ai/api/v1.

Streaming supported.

Request usage metadata when you need token/cost accounting.

## 6. Hugging Face

### Free-Tier Limits
> **Free account = $0.10/month of Inference Providers credit.** This is a **dollar-denominated credit, not a fixed token quota** — actual capacity depends entirely on the chosen model/provider's per-token price. No pay-as-you-go continuation after the credit is used on a Free account (PRO accounts can continue with paid usage after included credits).

| Feature | Free Account |
|---|---:|
| Inference Providers credit | $0.10/month |
| Pay-as-you-go after credit | ❌ |
| Models accessible | Thousands |
| Inference Providers ecosystem | 200+ models/providers |
| API / OpenAI-compatible API | ✅ / ✅ |
| Model download / Hub / Spaces | ✅ |
| ZeroGPU (Spaces) | Limited daily quota (shared/queued, not a dedicated free GPU server) |
| Dedicated Inference Endpoints | ❌ Paid only |
| Private model hosting | Limited |
| Fine-tuning | Generally paid (via Jobs/compute) |

### Credit example
$0.10 ÷ $0.20/1M tokens = 500,000 tokens available. $0.10 ÷ $2/1M tokens = only 50,000 tokens. Capacity is **model-price-dependent**, not a flat token allowance.

### Inference Providers
A single HF API/token routes to 200+ underlying model providers with centralized billing. A model being listed on HF does **not** guarantee free hosted inference exists for it — check the model page for available providers and pricing.

### Access
- Auth via personal token (`hf_xxxxxxxxxxxxxxxxx`), passed as `Authorization: Bearer hf_xxxxx`. Store as env var (`HF_TOKEN`); never expose in frontend code.
- Python: `huggingface_hub.InferenceClient` with an OpenAI-style `chat.completions.create()` interface.
- REST: OpenAI-compatible router at `https://router.huggingface.co/...`.

### Spaces
Host demo apps (Gradio, Streamlit, Docker) directly on HF infrastructure — useful for prototype hosting rather than API-based inference.

### Inference Providers vs. Inference Endpoints
| | Inference Providers | Inference Endpoints |
|---|---|---|
| Type | Shared serverless | Dedicated deployment |
| Cost | Small free credit, then pay-per-use | Paid only, billed by compute time |
| Free tier | $0.10/month | ❌ Requires active payment method |

---

## 7. Cloudflare

Three distinct free offerings: **Workers AI** (inference), **AI Gateway** (routing/observability), **AI Search / Vectorize** (RAG infra). Also **Cloudflare Workers** for general backend hosting.

### 7.1 Workers AI (Free)
| Resource | Free |
|---|---:|
| Daily inference budget | 10,000 Neurons/day |
| Reset | 00:00 UTC |
| Models available | 50+ open-source |
| Cost | $0 (blocked once exceeded, unless on Workers Paid plan) |

**Neuron** = GPU-compute unit consumed per model operation; cost varies by model.

Sample Neuron costs:
| Model | Input Neurons/1M tokens | Output Neurons/1M tokens |
|---|---:|---:|
| Llama 3.2 1B | 2,457 | 18,252 |
| Llama 3.2 3B | 4,625 | 30,475 |
| Llama 3.1 8B FP8 Fast | 4,119 | 34,868 |
| Llama 3.3 70B FP8 Fast | 26,668 | 204,805 |
| GPT-OSS-20B | 18,182 | 27,273 |
| GPT-OSS-120B | 31,818 | 68,182 |
| Gemma 3 12B | 31,371 | 50,560 |
| GLM-4.7 Flash | 5,500 | 36,400 |

Whisper (audio transcription):
| Model | Neurons/audio-minute | Free daily capacity |
|---|---:|---:|
| `@cf/openai/whisper` | 41.14 | ≈243 min (≈4.05 hrs) |
| `@cf/openai/whisper-large-v3-turbo` | 46.63 | ≈214 min (≈3.57 hrs) |

Example: Llama 3.2 1B processing 1M input tokens = 2,457 Neurons → free budget covers ≈4.07M input tokens/day from input alone (output tokens consume additional Neurons, reducing actual throughput).

**Task-type rate limits:** ASR 720 RPM · Image Classification 3,000 RPM · Image-to-Text 720 RPM · Object Detection 3,000 RPM · Summarization 1,500 RPM (additional model-specific limits apply). Note: the **10,000 Neurons/day** budget, not RPM, is the primary constraint.

### 7.2 Cloudflare Workers (general hosting, Free plan)
| Resource | Free |
|---|---:|
| Requests | 100,000/day |
| CPU | 10 ms/invocation |
| Memory | 128 MB |
| Subrequests | 50/request |
| Workers | 100/account |
| Cron triggers | 5/account |
| Request body | 100 MB |

### 7.3 AI Gateway (Free — core features free on all plans)
Routes/manages calls to Groq, Gemini, OpenAI, Anthropic, Workers AI, etc. through one gateway. Free features: analytics, caching, rate limiting, logging. **Does not provide model quota** — underlying provider's own quota/cost still applies.

| Feature | Free Limit |
|---|---:|
| Gateways | 10/account |
| Persistent logs | 100,000 total/account |
| Cacheable request size | 25 MB/request |
| Custom metadata | 5/request |
| Datasets | 10/gateway |
| Log size | 10 MB/log |
| Log rate | 500 logs/sec/gateway |

Supports custom **rate limits** (fixed or sliding window, scoped by user/model/app) and **spend limits** (dollar budget caps, e.g., $5/month, scoped by model/provider/user/team/app; blocks with `429` once reached, scopable via custom metadata).

### 7.4 AI Search (Free)
| Resource | Free |
|---|---:|
| Instances | 100/account |
| Namespaces | 100/account |
| Files | 100,000/instance |
| Max file size | 4 MB |
| Queries | 20,000/month |
| Pages crawled | 500/day |
| Metadata fields | 5 |

Includes **Vectorize** (vector DB) for RAG pipelines (chunk → embed → Vectorize → search → rerank → LLM).

---

## Cross-Provider Notes

Model-list availability ≠ successful generation. A provider can list a model while the specific request fails because of quota, modality, endpoint, temporary outage, or account restrictions.

400: usually inspect request format/capability before marking a model unavailable.

401/403: authentication or access issue.

404: model unavailable for the tested account/project or endpoint.

429: rate limit/quota; apply cooldown rather than permanent blacklist.

502/503: temporary upstream/provider failure.

Timeout: temporary network/provider issue; retry with bounded backoff.

Maintain a health registry keyed by provider + account/key + model + capability.

For EduScribe, maintain separate pools for text LLM, vision, transcription, TTS, embeddings, reranking, safety, and specialized agents.

Re-run model discovery periodically because provider catalogs change.

Current Recommended Normal-Text Pool

Provider

Recommended models from your successful tests

Groq

openai/gpt-oss-20b, openai/gpt-oss-120b, llama-3.3-70b-versatile, llama-3.1-8b-instant, qwen/qwen3.6-27b, groq/compound, groq/compound-mini

Gemini

models/gemma-4-26b-a4b-it, models/gemma-4-31b-it, models/gemini-flash-lite-latest, models/gemini-3-flash-preview, models/gemini-3.1-flash-lite, models/gemini-3.5-flash, models/gemini-3.5-flash-lite, models/gemini-3.6-flash, models/gemini-3.7-flash

Cohere

command-a-03-2025, command-r-plus-08-2024, command-r-08-2024, command-r7b-12-2024, c4ai-aya-expanse-32b

OpenRouter

nvidia/nemotron-3-super-120b-a12b:free, nvidia/nemotron-3-ultra-550b-a55b:free, nvidia/nemotron-3.5-lightning:free, liquid/lfm-2.5-2.6b:free, openrouter/free
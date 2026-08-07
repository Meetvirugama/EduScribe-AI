# 🎓 Educational Content Processing: Model Execution Plan
> **Objective:** This plan outlines the task-by-task execution strategy for processing educational content. For each task, it defines a 7-rank fallback model list across available providers.

## Phase 1 – Content Preparation (T01–T10)

Task:
Lecture Analysis

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Transcript Cleaning

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
OCR Text Cleaning

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Transcript + OCR Fusion

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Timestamp Alignment

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Frame Association

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Metadata Extraction

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Language Detection

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Content Normalization

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Semantic Chunking

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

## Phase 2 – Content Understanding (T11–T20)

Task:
Topic Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Subtopic Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Concept Extraction

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Keyword Extraction

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Learning Objective Detection

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Prerequisite Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Dependency Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Knowledge Tree Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Knowledge Gap Analysis

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Difficulty Classification

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

## Phase 3 – Knowledge Enrichment (T21–T35)

Task:
Definition Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Detailed Explanation Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Intuition Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Step-by-Step Explanation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Algorithm Explanation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Formula Explanation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Mathematical Derivation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Code Explanation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Pseudocode Generation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Complexity Analysis

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Proof / Reasoning Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Real-World Applications

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Industry Use Cases

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Historical Context

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Cross Topic References

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

## Phase 4 – Educational Enhancement (T36–T45)

Task:
Example Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Numerical Example Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Programming Example Generation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Visual Example Explanation

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Analogy Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Diagram Explanation

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Table Explanation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
OCR Context Integration

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Image Selection

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Screenshot Placement

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

## Phase 5 – Learning Support (T46–T53)

Task:
Common Mistakes Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Misconception Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Best Practices Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Edge Case Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Interview Perspective

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Practical Tips

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Important Notes Identification

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Learning Path Recommendation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

## Phase 6 – Note Organization (T54–T65)

Task:
Note Structuring

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Heading Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Section Organization

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
List Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Table Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Code Formatting

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Formula Formatting

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Image Positioning

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Reference Linking

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Markdown Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
HTML Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
PDF Generation

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

## Phase 7 – Quality Assurance (T66–T75)

Task:
Fact Verification

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Transcript Consistency Check

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
OCR Consistency Check

Capability:
Vision & Multimodal Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
State of the art vision understanding.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Fast and capable vision fallback.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/meta/llama-3.2-11b-vision-instruct

Reason:
Strong open-weight vision model.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moondream/moondream3.1-9B-A2B

Reason:
Fast and efficient vision reasoning.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/mistralai/mistral-small-3.1-24b-instruct

Reason:
Robust multimodal fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
nvidia/nemotron-nano-12b-v2-vl:free

Reason:
Free multimodal fallback.

--------------------------------

Rank 7

Provider:
Jina

Model:
jina-ai/jina-vlm

Reason:
Vision-language fallback model.

--------------------------------------------------

Task:
Duplicate Detection

Capability:
Embeddings & Vector Search

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-embedding-2

Reason:
Top quality multimodal embeddings.

--------------------------------

Rank 2

Provider:
Jina

Model:
jina-ai/jina-embeddings-v5-omni-small

Reason:
Excellent omni-modal embeddings.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/baai/bge-m3

Reason:
High-performance multilingual embeddings.

--------------------------------

Rank 4

Provider:
Jina

Model:
jina-ai/jina-embeddings-v4

Reason:
Strong fallback for text and image.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/google/embeddinggemma-300m

Reason:
Fast and lightweight embeddings.

--------------------------------

Rank 6

Provider:
Gemini

Model:
gemini-embedding-001

Reason:
Legacy reliable embedding model.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/baai/bge-large-en-v1.5

Reason:
Final fallback for text embeddings.

--------------------------------------------------

Task:
Completeness Check

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Missing Topic Detection

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Grammar & Language Refinement

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Readability Analysis

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Educational Quality Evaluation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Final Document Validation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

## Phase 8 – Search & AI Features (T76–T82)

Task:
Embedding Generation

Capability:
Embeddings & Vector Search

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-embedding-2

Reason:
Top quality multimodal embeddings.

--------------------------------

Rank 2

Provider:
Jina

Model:
jina-ai/jina-embeddings-v5-omni-small

Reason:
Excellent omni-modal embeddings.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/baai/bge-m3

Reason:
High-performance multilingual embeddings.

--------------------------------

Rank 4

Provider:
Jina

Model:
jina-ai/jina-embeddings-v4

Reason:
Strong fallback for text and image.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/google/embeddinggemma-300m

Reason:
Fast and lightweight embeddings.

--------------------------------

Rank 6

Provider:
Gemini

Model:
gemini-embedding-001

Reason:
Legacy reliable embedding model.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/baai/bge-large-en-v1.5

Reason:
Final fallback for text embeddings.

--------------------------------------------------

Task:
Embedding Optimization

Capability:
Embeddings & Vector Search

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-embedding-2

Reason:
Top quality multimodal embeddings.

--------------------------------

Rank 2

Provider:
Jina

Model:
jina-ai/jina-embeddings-v5-omni-small

Reason:
Excellent omni-modal embeddings.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/baai/bge-m3

Reason:
High-performance multilingual embeddings.

--------------------------------

Rank 4

Provider:
Jina

Model:
jina-ai/jina-embeddings-v4

Reason:
Strong fallback for text and image.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/google/embeddinggemma-300m

Reason:
Fast and lightweight embeddings.

--------------------------------

Rank 6

Provider:
Gemini

Model:
gemini-embedding-001

Reason:
Legacy reliable embedding model.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/baai/bge-large-en-v1.5

Reason:
Final fallback for text embeddings.

--------------------------------------------------

Task:
Vector Index Creation

Capability:
Embeddings & Vector Search

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-embedding-2

Reason:
Top quality multimodal embeddings.

--------------------------------

Rank 2

Provider:
Jina

Model:
jina-ai/jina-embeddings-v5-omni-small

Reason:
Excellent omni-modal embeddings.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/baai/bge-m3

Reason:
High-performance multilingual embeddings.

--------------------------------

Rank 4

Provider:
Jina

Model:
jina-ai/jina-embeddings-v4

Reason:
Strong fallback for text and image.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/google/embeddinggemma-300m

Reason:
Fast and lightweight embeddings.

--------------------------------

Rank 6

Provider:
Gemini

Model:
gemini-embedding-001

Reason:
Legacy reliable embedding model.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/baai/bge-large-en-v1.5

Reason:
Final fallback for text embeddings.

--------------------------------------------------

Task:
Semantic Search Indexing

Capability:
Embeddings & Vector Search

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-embedding-2

Reason:
Top quality multimodal embeddings.

--------------------------------

Rank 2

Provider:
Jina

Model:
jina-ai/jina-embeddings-v5-omni-small

Reason:
Excellent omni-modal embeddings.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/baai/bge-m3

Reason:
High-performance multilingual embeddings.

--------------------------------

Rank 4

Provider:
Jina

Model:
jina-ai/jina-embeddings-v4

Reason:
Strong fallback for text and image.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/google/embeddinggemma-300m

Reason:
Fast and lightweight embeddings.

--------------------------------

Rank 6

Provider:
Gemini

Model:
gemini-embedding-001

Reason:
Legacy reliable embedding model.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/baai/bge-large-en-v1.5

Reason:
Final fallback for text embeddings.

--------------------------------------------------

Task:
RAG Document Preparation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Knowledge Graph Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Metadata Indexing

Capability:
Embeddings & Vector Search

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-embedding-2

Reason:
Top quality multimodal embeddings.

--------------------------------

Rank 2

Provider:
Jina

Model:
jina-ai/jina-embeddings-v5-omni-small

Reason:
Excellent omni-modal embeddings.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/baai/bge-m3

Reason:
High-performance multilingual embeddings.

--------------------------------

Rank 4

Provider:
Jina

Model:
jina-ai/jina-embeddings-v4

Reason:
Strong fallback for text and image.

--------------------------------

Rank 5

Provider:
Cloudflare

Model:
@cf/google/embeddinggemma-300m

Reason:
Fast and lightweight embeddings.

--------------------------------

Rank 6

Provider:
Gemini

Model:
gemini-embedding-001

Reason:
Legacy reliable embedding model.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/baai/bge-large-en-v1.5

Reason:
Final fallback for text embeddings.

--------------------------------------------------

## Phase 9 – Future Features (T83–T90)

Task:
Flashcard Generation

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Quiz Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Mind Map Generation

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
AI Tutor Knowledge Base

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Personalized Learning Metadata

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Study Progress Analytics

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Concept Relationship Graph

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Learning Recommendation Engine

Capability:
Complex Reasoning & Long Context Analysis

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
Highest quality and longest context for complex analysis.

--------------------------------

Rank 2

Provider:
Cohere

Model:
command-a-plus-05-2026

Reason:
Excellent long-context alternative with strong reasoning.

--------------------------------

Rank 3

Provider:
OpenRouter

Model:
nvidia/nemotron-3-ultra-550b-a55b:free

Reason:
High reasoning capability fallback.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

## Phase 10 – System Management (T91–T100)

Task:
Prompt Selection

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Prompt Version Management

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
LLM Model Selection

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Provider Routing

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Retry Management

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Fallback Management

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Token Optimization

Capability:
Cleaning, Formatting & Fast Processing

Execution Priority

Rank 1

Provider:
Gemini

Model:
gemini-2.5-flash

Reason:
Highest speed and quality for text processing.

--------------------------------

Rank 2

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
Very fast fallback with excellent quality.

--------------------------------

Rank 3

Provider:
Cohere

Model:
command-a-03-2025

Reason:
Strong long-context understanding.

--------------------------------

Rank 4

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.6

Reason:
Large context and reliable structured output.

--------------------------------

Rank 5

Provider:
Groq

Model:
qwen/qwen3.6-27b

Reason:
Efficient reasoning fallback.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Free high-quality fallback.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-20b

Reason:
Fast and reliable local fallback.

--------------------------------------------------

Task:
Context Window Management

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Cost Tracking

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------

Task:
Processing Logs & Monitoring

Capability:
Code & Math Generation

Execution Priority

Rank 1

Provider:
Cloudflare

Model:
@cf/moonshotai/kimi-k2.7-code

Reason:
Excellent coding and structural reasoning.

--------------------------------

Rank 2

Provider:
Gemini

Model:
gemini-2.5-pro

Reason:
High capability in logical and mathematical tasks.

--------------------------------

Rank 3

Provider:
Cloudflare

Model:
@cf/qwen/qwen2.5-coder-32b-instruct

Reason:
Specialized and powerful coding model.

--------------------------------

Rank 4

Provider:
OpenRouter

Model:
cohere/north-mini-code:free

Reason:
Free coding model fallback.

--------------------------------

Rank 5

Provider:
Groq

Model:
llama-3.3-70b-versatile

Reason:
General purpose fallback for logic.

--------------------------------

Rank 6

Provider:
OpenRouter

Model:
google/gemma-4-31b-it:free

Reason:
Solid instruction following.

--------------------------------

Rank 7

Provider:
Cloudflare

Model:
@cf/openai/gpt-oss-120b

Reason:
Final production fallback.

--------------------------------------------------


## API Key Rotation Strategy

Example

Gemini

API Key 1
↓

API Key 2
↓

API Key 3
↓

API Key 4

↓

Switch Provider

↓

Groq

↓

Cloudflare

↓

OpenRouter

↓

Cohere

--------------------------------------------------

## Explanation of Selected Execution Order

The execution priority lists above have been constructed by meticulously selecting only the available models from the configured providers (Gemini, Groq, Cloudflare, OpenRouter, Cohere, Hugging Face, Jina). The rankings are systematically structured to balance output quality, context length, latency, cost, and reliability without relying on unavailable providers (like OpenAI directly or Anthropic).

**1. Primary Execution (Rank 1 & 2):** 
We consistently place Gemini (Pro or Flash) or Cloudflare's Kimi / Moonshot models at Rank 1. Gemini provides industry-leading multimodal, long-context reasoning with high API stability, backed by 4 keys. Cohere's Command models (A-plus and A-reasoning) or Groq's high-speed inference (Llama-3.3-70b-versatile) are typically used as Rank 2 depending on the capability (reasoning vs. speed), providing massive context window capacities and low latency.

**2. Specialized Capabilities:** 
- **Vision:** We fallback to Cloudflare's Llama-3.2-11b-vision-instruct and Moondream, which offer excellent vision reasoning without the high cost.
- **Code:** We prioritize Moonshot Kimi K2.7 and Qwen2.5-Coder on Cloudflare for their structured output quality and algorithmic reasoning. 
- **Embeddings:** Gemini-Embedding-2 and Jina Omni/v5 models are prioritized, leveraging Jina's highly specialized embedding capabilities and Gemini's multimodal excellence.

**3. Robust Fallback Tiers (Rank 3 to 7):**
- As we proceed down the list, we prioritize OpenRouter's free tier for heavy open-weight models (like Nemotron-3-Ultra 550B and Gemma-4-31B). These serve as emergency high-quality fallback options that do not consume paid quota.
- Finally, Cloudflare's OSS deployments (gpt-oss-120b/20b) and Groq's Qwen/Llama deployments act as the final, highly reliable production fallbacks ensuring 99.9% uptime for the entire pipeline.

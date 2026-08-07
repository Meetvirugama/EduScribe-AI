# Hugging Face Inference Providers

Hugging Face’s Inference Providers give developers access to hundreds of machine learning models, powered by world-class inference providers. They are also integrated into HF client SDKs (for JS and Python), making it easy to explore serverless inference of models on your favorite providers.

## Why Choose Inference Providers?

When you build AI applications, it’s tough to manage multiple provider APIs, comparing model performance, and dealing with varying reliability. Inference Providers solves these challenges by offering:

- **Instant Access to Cutting-Edge Models:** Go beyond mainstream providers to access thousands of specialized models across multiple AI tasks. Whether you need the latest language models, state-of-the-art image generators, or domain-specific embeddings, you’ll find them here.
- **Zero Vendor Lock-in:** Unlike being tied to a single provider’s model catalog, you get access to models from Cerebras, Groq, Together AI, Replicate, and more — all through one consistent interface.
- **Production-Ready Performance:** Built for enterprise workloads with the reliability your applications demand.

### What you can build:

- **Text Generation:** Use Large language models with tool-calling capabilities for chatbots, content generation, and code assistance.
- **Image and Video Generation:** Create custom images and videos, including support for LoRAs and style customization.
- **Search & Retrieval:** State-of-the-art embeddings for semantic search, RAG systems, and recommendation engines.
- **Traditional ML Tasks:** Ready-to-use models for classification, NER, summarization, and speech recognition.

## Key Features

- **All-in-One API:** A single API for text generation, image generation, document embeddings, NER, summarization, image classification, and more.
- **Multi-Provider Support:** Easily run models from top-tier providers like fal, Replicate, Together AI, and others.
- **Scalable & Reliable:** Built for high availability and low-latency performance in production environments.
- **Developer-Friendly:** Simple requests, fast responses, and a consistent developer experience across Python and JavaScript clients.
- **Easy to integrate:** Drop-in replacement for the OpenAI chat completions API.
- **Cost-Effective:** No extra markup on provider rates.

## Provider Selection

The Inference Providers API acts as a unified proxy layer that sits between your application and multiple AI providers.

### Provider Selection Policy Suffixes

You can append a policy suffix to the model id to change the provider selection:
- `:fastest` (default): Selects the fastest available provider for the model (highest throughput).
- `:cheapest`: Selects the most cost-efficient provider (lowest price per output token).
- `:preferred`: Follows your preference order in Inference Provider settings.
- `:<provider_name>` (e.g., `:groq`): Selects a specific provider.

## OpenAI-Compatible Chat Completions Endpoint

If you prefer to work with familiar OpenAI APIs or want to migrate existing chat completion code with minimal changes, HF offers a drop-in compatible endpoint that handles all provider selection automatically on the server side.

**Endpoint:** `https://router.huggingface.co/v1/chat/completions`

### Example using Python (OpenAI SDK / LiteLLM)

```python
import os
from openai import OpenAI

client = OpenAI(
  baseURL="https://router.huggingface.co/v1",
  apiKey=os.environ.get("HF_TOKEN"),
)

completion = client.chat.completions.create(
  model="deepseek-ai/DeepSeek-R1:fastest",
  messages=[{"role": "user", "content": "Hello!"}],
)

print(completion.choices[0].message)
```

### Example using HTTP / cURL

```bash
curl https://router.huggingface.co/v1/chat/completions \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1:fastest",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

*Note: This OpenAI-compatible endpoint is currently available for chat completion tasks only.*

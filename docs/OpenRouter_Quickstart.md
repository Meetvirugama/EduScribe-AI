# OpenRouter Quickstart

OpenRouter provides a unified API that gives you access to hundreds of AI models through a single endpoint, while automatically handling fallbacks and selecting the most cost-effective options.

There are three ways to integrate with OpenRouter, depending on how much control you want:

| Approach | Best for |
| --- | --- |
| **API** | Full control, any language, no dependencies |
| **Client SDKs** | Type-safe model calls with minimal overhead |
| **Agent SDK** | Building agents with tool use, loops, and state |

---

## 1. Using the OpenRouter API

The most direct way to use OpenRouter. Send standard HTTP requests to the `/api/v1/chat/completions` endpoint — compatible with any language or framework.

### Example (cURL)
```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "HTTP-Referer: <YOUR_SITE_URL>" \
  -H "X-OpenRouter-Title: <YOUR_SITE_NAME>" \
  -d '{
  "model": "openai/gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
}'
```
*Note: The `HTTP-Referer` and `X-OpenRouter-Title` headers are optional, but setting them allows your app to appear on the OpenRouter leaderboards.*

---

## 2. Using the Client SDKs

The Client SDKs wrap the OpenRouter API with full type safety, auto-generated types from the OpenAPI spec, and zero boilerplate.

### TypeScript
```bash
npm install @openrouter/sdk
```

```typescript
import { OpenRouter } from '@openrouter/sdk';

const client = new OpenRouter({
  apiKey: '<OPENROUTER_API_KEY>',
});

const completion = await client.chat.send({
  model: 'openai/gpt-4o',
  messages: [
    { role: 'user', content: 'What is the meaning of life?' },
  ],
});
console.log(completion.choices[0].message.content);
```

### Python
```bash
pip install openrouter
```

```python
from openrouter import OpenRouter
import os

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    response = client.chat.send(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "What is the meaning of life?"}],
    )
    print(response.choices[0].message.content)
```

---

## 3. Using the Agent SDK

The Agent SDK (`@openrouter/agent`) provides higher-level primitives for building AI agents. It handles multi-turn conversation loops, tool execution, and state management automatically.

```bash
npm install @openrouter/agent
```

```typescript
import { OpenRouter, tool } from '@openrouter/agent';
import { z } from 'zod';

const openrouter = new OpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

const weatherTool = tool({
  name: 'get_weather',
  description: 'Get the current weather for a location',
  inputSchema: z.object({
    location: z.string().describe('City name'),
  }),
  execute: async ({ location }) => {
    return { temperature: 72, condition: 'sunny', location };
  },
});

const result = openrouter.callModel({
  model: 'anthropic/claude-3.5-sonnet',
  messages: [{ role: 'user', content: 'What is the weather in San Francisco?' }],
  tools: [weatherTool],
});

const text = await result.getText();
console.log(text);
```

---

## 4. Using the OpenAI SDK (Drop-in Replacement)

You can use the OpenAI SDK pointed at OpenRouter as a drop-in replacement. This is useful if you have existing code built on the OpenAI SDK and want to access OpenRouter's model catalog without changing your code structure.

### Python (LiteLLM/OpenAI)

```python
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="<OPENROUTER_API_KEY>",
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>",
    "X-OpenRouter-Title": "<YOUR_SITE_NAME>",
  },
  model="mistralai/mistral-7b-instruct:free",
  messages=[
    {"role": "user", "content": "What is the meaning of life?"}
  ]
)
print(completion.choices[0].message.content)
```

By changing the `base_url` to `https://openrouter.ai/api/v1`, you can instantly use OpenAI client tools to query OpenRouter models!

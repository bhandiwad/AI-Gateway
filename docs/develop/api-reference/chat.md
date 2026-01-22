# Chat Completions

The chat completions endpoint is fully compatible with the OpenAI API format.

---

## `POST /api/v1/chat/completions`

Creates a chat completion.

### Request

```bash
curl http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | ✓ | Model ID (e.g., `gpt-4o-mini`, `claude-3-sonnet`) |
| `messages` | array | ✓ | Array of message objects |
| `temperature` | float | | Sampling temperature (0-2). Default: 1 |
| `max_tokens` | integer | | Maximum tokens to generate |
| `top_p` | float | | Nucleus sampling (0-1). Default: 1 |
| `stream` | boolean | | Enable streaming. Default: false |
| `stop` | array | | Stop sequences |
| `presence_penalty` | float | | Presence penalty (-2 to 2) |
| `frequency_penalty` | float | | Frequency penalty (-2 to 2) |
| `user` | string | | User identifier for tracking |

### Message object

```json
{
  "role": "user",      // "system", "user", or "assistant"
  "content": "Hello!"  // Message content
}
```

### Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677858242,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

---

## Streaming

Enable streaming to receive responses in real-time.

### Request

```bash
curl http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

### Response (Server-Sent Events)

```
data: {"id":"chatcmpl-abc","choices":[{"delta":{"role":"assistant"}}]}

data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":"Once"}}]}

data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":" upon"}}]}

data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":" a"}}]}

data: [DONE]
```

---

## Python examples

### Basic usage

```python
import openai

client = openai.OpenAI(
    api_key="sk-gw-your-key",
    base_url="http://localhost:8000/api/v1"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
)

print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### With parameters

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Be creative!"}],
    temperature=0.9,
    max_tokens=500,
    top_p=0.95,
    presence_penalty=0.5
)
```

---

## Supported models

### OpenAI

| Model | Description |
|-------|-------------|
| `gpt-4o` | Latest GPT-4 Omni |
| `gpt-4o-mini` | Fast, cost-effective |
| `gpt-4-turbo` | GPT-4 Turbo |
| `gpt-3.5-turbo` | Fast, affordable |

### Anthropic

| Model | Description |
|-------|-------------|
| `claude-3-5-sonnet-20241022` | Latest Claude 3.5 |
| `claude-3-opus-20240229` | Most capable |
| `claude-3-sonnet-20240229` | Balanced |
| `claude-3-haiku-20240307` | Fastest |

### Google

| Model | Description |
|-------|-------------|
| `gemini-2.0-flash` | Latest Gemini |
| `gemini-1.5-pro` | Most capable |
| `gemini-1.5-flash` | Fast |

---

## Error handling

```python
from openai import APIError, RateLimitError

try:
    response = client.chat.completions.create(...)
except RateLimitError:
    print("Rate limited - wait and retry")
except APIError as e:
    print(f"API error: {e}")
```

---

## Rate limits

Rate limits are applied per API key:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per minute |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Reset timestamp |


# Develop

Build powerful AI applications with AI Gateway.

---

## Documentation

| Section | Description |
|---------|-------------|
| **[API Reference](api-reference/index.md)** | Complete reference for all API endpoints with examples. |
| **[Concepts](concepts/index.md)** | Deep dive into guardrails, routing, and authentication. |

---

## Quick reference

### Chat completions

```python
import openai

client = openai.OpenAI(
    api_key="sk-gw-your-key",
    base_url="http://localhost:8000/api/v1"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### With streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

### Test guardrails

```bash
curl -X POST http://localhost:8000/api/v1/admin/guardrails/test \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text": "My SSN is 123-45-6789", "policy": "default"}'
```

---

## Popular topics

| Topic | Description |
|-------|-------------|
| [Chat Completions](api-reference/chat.md) | OpenAI-compatible chat API |
| [API Keys](api-reference/api-keys.md) | Create and manage API keys |
| [Guardrails](concepts/guardrails.md) | PII detection, prompt injection |
| [Routing](concepts/routing.md) | Multi-provider routing strategies |
| [SSO](concepts/sso.md) | Single sign-on integration |
| [Rate Limiting](concepts/rate-limiting.md) | Request and token limits |


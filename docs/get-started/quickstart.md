# Quickstart

Make your first API call in under 5 minutes! 

---

## Step 1: Start AI Gateway

If you haven't already, start AI Gateway:

```bash
docker-compose up -d
```

---

## Step 2: Create an account

=== "Using cURL"

    ```bash
    curl -X POST http://localhost:8000/api/v1/admin/auth/register \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Your Name",
        "email": "you@example.com",
        "password": "SecurePassword123!"
      }'
    ```

=== "Using the Dashboard"

    1. Open http://localhost in your browser
    2. Click **Sign Up**
    3. Fill in your details and click **Register**

You'll receive an access token in the response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "tenant": {
    "id": 1,
    "name": "Your Name",
    "email": "you@example.com"
  }
}
```

---

## Step 3: Create an API key

Use your access token to create an API key:

```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Key"}'
```

Response:

```json
{
  "id": 1,
  "name": "My First Key",
  "api_key": "sk-gw-abc123...",  // Save this!
  "key_prefix": "sk-gw-abc"
}
```

!!! warning "Save your API key"
    The full API key is only shown once. Store it securely!

---

## Step 4: Make your first request

Use your API key to make a chat completion request:

```bash
curl http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer sk-gw-abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello! What can you do?"}
    ]
  }'
```

Response:

```json
{
  "id": "chatcmpl-abc123",
  "model": "gpt-4o-mini",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! I'm an AI assistant..."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 45,
    "total_tokens": 57
  }
}
```

 **Congratulations!** You've made your first API call through AI Gateway!

---

## Step 5: Try with Python

```python
import openai

client = openai.OpenAI(
    api_key="sk-gw-abc123...",  # Your AI Gateway key
    base_url="http://localhost:8000/api/v1"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

!!! tip "OpenAI SDK Compatible"
    AI Gateway is fully compatible with the OpenAI Python SDK. Just change the `base_url`!

---

## What's happening under the hood?

```
Your Request
     │
     ▼
┌─────────────┐
│ AI Gateway  │──▶ Authentication
│             │──▶ Rate Limiting
│             │──▶ Input Guardrails (PII, injection)
│             │──▶ Route to Provider
│             │──▶ Output Guardrails
│             │──▶ Usage Logging
└─────────────┘
     │
     ▼
  Response
```

AI Gateway automatically:
- :shield: Applies security guardrails
- :chart_with_upwards_trend: Tracks usage and costs
- :arrows_counterclockwise: Handles retries and failover
- :memo: Logs for audit compliance

---

## Next steps



-    **Learn the concepts**

    Understand tenants, API keys, guardrails, and routing.

    [ Main concepts](concepts.md)

-    **Configure guardrails**

    Set up PII detection and prompt injection protection.

    [ Guardrails](../develop/concepts/guardrails.md)

-    **Explore routing**

    Learn about multi-provider routing and fallback strategies.

    [ Routing](../develop/concepts/routing.md)

-    **API Reference**

    Complete API documentation with examples.

    [ API Reference](../develop/api-reference/index.md)




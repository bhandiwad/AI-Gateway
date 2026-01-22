# 📡 API Reference

Complete API documentation for AI Gateway. All endpoints are prefixed with `/api/v1`.

---

## Authentication

### Register New Tenant

```http
POST /api/v1/admin/auth/register
Content-Type: application/json

{
  "name": "Your Name",
  "email": "you@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "tenant": {
    "id": 1,
    "name": "Your Name",
    "email": "you@example.com",
    "is_active": true,
    "is_admin": false,
    "rate_limit": 100,
    "monthly_budget": 100.0,
    "current_spend": 0.0
  }
}
```

### Login

```http
POST /api/v1/admin/auth/login
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "tenant": { ... }
}
```

### Get Current User

```http
GET /api/v1/admin/auth/me
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Your Name",
  "email": "you@example.com",
  "is_admin": false
}
```

---

## Chat Completions

OpenAI-compatible chat completion API.

### Create Chat Completion

```http
POST /api/v1/chat/completions
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model ID (e.g., "gpt-4", "claude-3-opus") |
| `messages` | array | Yes | Array of message objects |
| `temperature` | float | No | Sampling temperature (0-2) |
| `max_tokens` | integer | No | Maximum tokens to generate |
| `top_p` | float | No | Nucleus sampling parameter |
| `stream` | boolean | No | Enable streaming response |
| `stop` | array | No | Stop sequences |
| `presence_penalty` | float | No | Presence penalty (-2 to 2) |
| `frequency_penalty` | float | No | Frequency penalty (-2 to 2) |

**Response (200 OK):**
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

### Streaming Response

With `stream: true`, response is Server-Sent Events:

```
data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":"Hello"}}]}

data: {"id":"chatcmpl-abc123","choices":[{"delta":{"content":"!"}}]}

data: [DONE]
```

---

## API Keys

### Create API Key

```http
POST /api/v1/admin/api-keys
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Production Key",
  "description": "Key for production environment",
  "environment": "production",
  "rate_limit_override": 500,
  "allowed_models_override": ["gpt-4", "gpt-3.5-turbo"],
  "cost_limit_daily": 50.0,
  "cost_limit_monthly": 500.0
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Production Key",
  "api_key": "sk-gw-abc123...",
  "key_prefix": "sk-gw-abc",
  "is_active": true,
  "environment": "production",
  "rate_limit_override": 500,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List API Keys

```http
GET /api/v1/admin/api-keys
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Production Key",
    "key_prefix": "sk-gw-abc",
    "is_active": true,
    "environment": "production",
    "last_used_at": "2024-01-15T12:00:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Revoke API Key

```http
DELETE /api/v1/admin/api-keys/{key_id}
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
{
  "message": "API key revoked successfully"
}
```

---

## Router Configuration

### Get Router Config

```http
GET /api/v1/admin/router/config
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
{
  "default_provider": "openai",
  "default_model": "gpt-4o-mini",
  "strategies": [
    {
      "name": "cost_optimized",
      "description": "Route to cheapest model",
      "priority_order": ["gpt-4o-mini", "claude-3-haiku"],
      "enabled": false
    },
    {
      "name": "balanced",
      "description": "Balance cost and quality",
      "priority_order": ["gpt-4o", "claude-3-5-sonnet"],
      "enabled": true
    }
  ],
  "fallback": {
    "enabled": true,
    "max_retries": 3,
    "fallback_order": ["openai", "anthropic"]
  }
}
```

### List Providers

```http
GET /api/v1/admin/router/providers
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
{
  "providers": [
    {
      "name": "openai",
      "type": "openai",
      "is_active": true,
      "priority": 1,
      "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
      "status": "healthy",
      "has_api_key": true
    }
  ]
}
```

### Provider Health

```http
GET /api/v1/admin/router/health
Authorization: Bearer YOUR_TOKEN
```

---

## Guardrails

### List Guardrails

```http
GET /api/v1/admin/guardrails
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
{
  "guardrails": [
    {
      "id": "pii_detection",
      "name": "PII Detection",
      "description": "Detects and redacts PII",
      "actions": ["redact", "block", "warn"],
      "bfsi_relevant": true
    }
  ]
}
```

### Test Guardrails

```http
POST /api/v1/admin/guardrails/test
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "My SSN is 123-45-6789",
  "policy": "default",
  "is_input": true
}
```

**Response (200 OK):**
```json
{
  "original_text": "My SSN is 123-45-6789",
  "processed_text": "My SSN is [SSN_REDACTED]",
  "blocked": false,
  "warnings": [],
  "triggered_guardrails": [
    {"type": "pii_detection", "detected_types": ["ssn"]}
  ],
  "actions_taken": ["redacted_pii"]
}
```

### List Policies

```http
GET /api/v1/admin/guardrails/policies
Authorization: Bearer YOUR_TOKEN
```

### BFSI Guardrails

```http
GET /api/v1/admin/guardrails/bfsi
Authorization: Bearer YOUR_TOKEN
```

---

## Tenants (Admin)

### List Tenants

```http
GET /api/v1/admin/tenants
Authorization: Bearer ADMIN_TOKEN
```

### Get Tenant

```http
GET /api/v1/admin/tenants/{tenant_id}
Authorization: Bearer YOUR_TOKEN
```

### Update Tenant

```http
PATCH /api/v1/admin/tenants/{tenant_id}
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Updated Name",
  "rate_limit": 500,
  "monthly_budget": 1000.0,
  "allowed_models": ["gpt-4", "gpt-3.5-turbo"]
}
```

---

## Users

### List Users

```http
GET /api/v1/admin/users
Authorization: Bearer YOUR_TOKEN
```

### Create User

```http
POST /api/v1/admin/users
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "New User",
  "role": "user"
}
```

### Update User

```http
PATCH /api/v1/admin/users/{user_id}
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Updated Name",
  "role": "admin"
}
```

### Delete User

```http
DELETE /api/v1/admin/users/{user_id}
Authorization: Bearer YOUR_TOKEN
```

---

## Usage & Billing

### Usage Summary

```http
GET /api/v1/admin/usage/summary
Authorization: Bearer YOUR_TOKEN
```

### Dashboard Stats

```http
GET /api/v1/admin/dashboard/stats
Authorization: Bearer YOUR_TOKEN
```

**Response (200 OK):**
```json
{
  "total_requests": 15234,
  "total_tokens": 1523400,
  "total_cost": 45.67,
  "requests_today": 523,
  "cost_today": 2.34
}
```

---

## Audit Logs

### List Audit Logs

```http
GET /api/v1/admin/audit-logs
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Filter by action type |
| `start_date` | string | Start date (ISO format) |
| `end_date` | string | End date (ISO format) |
| `limit` | integer | Max results (default: 100) |
| `offset` | integer | Pagination offset |

---

## Alerts

### List Alerts

```http
GET /api/v1/admin/alerts
Authorization: Bearer YOUR_TOKEN
```

### Create Alert

```http
POST /api/v1/admin/alerts
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "High Usage Alert",
  "type": "usage_threshold",
  "threshold": 10000,
  "enabled": true
}
```

---

## SSO

### List SSO Providers

```http
GET /api/v1/admin/auth/sso/providers
```

### OIDC Discovery

```http
POST /api/v1/admin/sso/discover
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "issuer_url": "https://accounts.google.com"
}
```

### Initiate SSO Login

```http
POST /api/v1/admin/auth/sso/initiate
Content-Type: application/json

{
  "provider_name": "google",
  "redirect_uri": "https://your-app.com/callback"
}
```

### SSO Callback

```http
GET /api/v1/admin/auth/sso/callback?code=AUTH_CODE&state=STATE&provider_name=google
```

---

## Health & Metrics

### Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

### Metrics

```http
GET /metrics
```

### Feature Status

```http
GET /api/v1/admin/features/status
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```


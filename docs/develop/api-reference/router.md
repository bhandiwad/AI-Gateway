# Router API

Endpoints for managing routing configuration and providers.

---

## Get Router Config {#config}

```http
GET /api/v1/admin/router/config
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
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

---

## List Providers {#providers}

```http
GET /api/v1/admin/router/providers
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
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
    },
    {
      "name": "anthropic",
      "type": "anthropic",
      "is_active": true,
      "priority": 2,
      "models": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
      "status": "healthy",
      "has_api_key": true
    }
  ]
}
```

---

## Provider Health {#health}

```http
GET /api/v1/admin/router/health
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "providers": [
    {
      "name": "openai",
      "status": "healthy",
      "latency_ms": 234,
      "success_rate": 99.5,
      "last_check": "2024-01-15T12:00:00Z"
    },
    {
      "name": "anthropic",
      "status": "degraded",
      "latency_ms": 890,
      "success_rate": 95.2,
      "last_check": "2024-01-15T12:00:00Z"
    }
  ]
}
```

---

## Test Routing

```http
POST /api/v1/admin/router/test
Authorization: Bearer YOUR_TOKEN
```

**Request:**
```json
{
  "model": "gpt-4"
}
```

**Response (200):**
```json
{
  "success": true,
  "model": "gpt-4",
  "provider": "openai",
  "latency_ms": 245,
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 2
  }
}
```

# Routing

AI Gateway intelligently routes requests across multiple AI providers.

---

## Overview

The router selects the best provider for each request based on:

- **Routing strategy** (cost, quality, balanced)
- **Provider health** (availability, latency)
- **Model availability** (which provider has the model)
- **Tenant configuration** (allowed providers/models)

```
Request
   │
   ▼
┌─────────────────┐
│     Router      │
├─────────────────┤
│ 1. Check health │
│ 2. Apply rules  │
│ 3. Select best  │
└────────┬────────┘
         │
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│ OpenAI │ │Anthropic│ │ Google │
└────────┘ └────────┘ └────────┘
```

---

## Routing strategies

### Cost optimized

Routes to the cheapest available provider/model.

```
Priority: gpt-4o-mini → claude-3-haiku → gpt-3.5-turbo
```

**Best for:** High-volume, cost-sensitive workloads

### Quality first

Routes to the highest quality model.

```
Priority: gpt-4o → claude-3-opus → gemini-pro
```

**Best for:** Complex tasks requiring best results

### Balanced

Balances between cost and quality.

```
Priority: gpt-4o-mini → claude-3-sonnet → gpt-4
```

**Best for:** General purpose workloads

---

## Fallback & retry

When a provider fails, the router automatically tries alternatives:

```
Request → OpenAI (timeout) → Anthropic (error) → Google (success!)
              │                   │
              └─── Retry 3x ──────┘
```

### Configuration

```json
{
  "fallback": {
    "enabled": true,
    "max_retries": 3,
    "fallback_order": ["openai", "anthropic", "google"]
  }
}
```

---

## Load balancing

Distribute requests across providers for optimal performance.

### Strategies

| Strategy | Description |
|----------|-------------|
| Round-robin | Equal distribution |
| Weighted | Based on priority weights |
| Least-connections | Route to least busy |

### Example

```json
{
  "load_balancing": {
    "enabled": true,
    "strategy": "weighted",
    "weights": {
      "openai": 60,
      "anthropic": 30,
      "google": 10
    }
  }
}
```

---

## Circuit breaker

Automatically stops sending requests to unhealthy providers.

```
Healthy → Failures → Open (skip) → Half-open (test) → Healthy
                         │                │
                         └── 30s cooldown ─┘
```

### States

| State | Behavior |
|-------|----------|
| **Closed** | Normal operation |
| **Open** | Skip provider |
| **Half-open** | Test with single request |

---

## Provider health

Check provider health status:

```bash
GET /api/v1/admin/router/health
```

**Response:**

```json
{
  "providers": [
    {
      "name": "openai",
      "status": "healthy",
      "latency_ms": 234,
      "success_rate": 99.5
    },
    {
      "name": "anthropic",
      "status": "degraded",
      "latency_ms": 890,
      "success_rate": 95.2
    }
  ]
}
```

---

## Model mapping

Map model aliases to specific providers:

```json
{
  "model_mapping": {
    "gpt-4": "openai/gpt-4-turbo",
    "claude": "anthropic/claude-3-sonnet",
    "fast": "openai/gpt-4o-mini"
  }
}
```

Usage:
```json
{"model": "fast"}  // Routes to gpt-4o-mini
```

---

## Best practices

!!! tip "Enable fallbacks"
    Always configure fallback providers for resilience.

!!! tip "Monitor health metrics"
    Set up alerts for provider degradation.

!!! tip "Use cost-optimized for development"
    Save costs during development with cheaper models.

!!! tip "Test routing regularly"
    Verify failover works before you need it.


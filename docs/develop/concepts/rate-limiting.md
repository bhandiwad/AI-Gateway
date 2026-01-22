# Rate Limiting

Control request rates to protect your AI Gateway and manage costs.

---

## Overview

AI Gateway supports rate limiting at multiple levels:

| Level | Description |
|-------|-------------|
| **Tenant** | Default limit for all requests from a tenant |
| **API Key** | Override limit for specific API keys |
| **User** | Per-user limits within a tenant |

---

## How It Works

```
Request → Check Tenant Limit → Check API Key Limit → Process or Reject
                 │                      │
                 ▼                      ▼
           429 if exceeded        429 if exceeded
```

---

## Configuration

### Tenant Rate Limit

Set via tenant update:

```bash
PATCH /api/v1/admin/tenants/{tenant_id}
{
  "rate_limit": 100  # requests per minute
}
```

### API Key Override

Create key with custom limit:

```bash
POST /api/v1/admin/api-keys
{
  "name": "High Volume Key",
  "rate_limit_override": 500
}
```

---

## Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

---

## Handling 429 Errors

When rate limited, implement exponential backoff:

```python
import time
import random

def make_request_with_retry(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait = (2 ** attempt) + random.random()
            time.sleep(wait)
    raise Exception("Max retries exceeded")
```

---

## Best Practices

1. **Use appropriate limits** - Set limits based on actual usage patterns
2. **Implement backoff** - Handle 429 errors gracefully
3. **Distribute load** - Use multiple API keys if needed
4. **Monitor usage** - Track rate limit hits in dashboard
